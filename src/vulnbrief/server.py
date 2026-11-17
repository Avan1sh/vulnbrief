"""Local analyst workbench; one queued agent at a time, server-side credentials."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import csv
import io
import json
import os
from pathlib import Path
from threading import Lock
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .agent import Investigator
from .history import History, compare_reports
from .inventory import load_context
from .llm import GroqLLM
from .models import Context, StrictModel
from .tools import ToolKit
from .trace import Trace


class StartRun(StrictModel):
    goal: str = Field(min_length=8,max_length=8000)
    inventory_text: str = Field(default='',max_length=50000)
    inventory_format: str = Field(default='json',pattern=r'^(json|csv)$')
    inject_failure: bool = False
    model: str = Field(default='openai/gpt-oss-120b',pattern=r'^openai/gpt-oss-(120b|20b)$')


class TaskReview(StrictModel):
    status: str = Field(pattern=r'^(draft|accepted|dismissed)$')
    review_note: str = Field(default='',max_length=1500)
    owner: str = Field(default='Unassigned',max_length=120)


def create_app(project: Path | None = None, storage: Path | None = None, runner=None):
    project=(project or Path.cwd()).resolve()
    storage=(storage or project/'.vulnbrief').resolve()
    storage.mkdir(parents=True,exist_ok=True)
    (storage/'inputs').mkdir(exist_ok=True)
    history=History(storage/'history.sqlite3')
    executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='vulnbrief')
    launch_lock=Lock()
    load_dotenv(project/'.env',override=False)

    @asynccontextmanager
    async def lifespan(app):
        history.recover_interrupted()
        for prefix in ('final-*','v02-*'):
            for path in (project/'artifacts').glob(prefix+'/report.json'):
                try:
                    report=json.loads(path.read_text(encoding='utf-8'))
                    history.save(report,path.parent)
                except (ValueError,KeyError):
                    continue
        yield
        executor.shutdown(wait=False,cancel_futures=True)

    app=FastAPI(title='VulnBrief workbench',version='0.2.0',lifespan=lifespan)
    app.state.history=history
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','testserver'])

    @app.middleware('http')
    async def local_requests(request:Request,call_next):
        if request.method in {'POST','PUT','PATCH','DELETE'}:
            origin=request.headers.get('origin')
            if origin and origin!=str(request.base_url).rstrip('/'):
                return Response('Cross-origin writes are disabled',status_code=403)
            if int(request.headers.get('content-length','0'))>100000:
                return Response('Request exceeds local inventory limit',status_code=413)
        return await call_next(request)

    def existing(run_id):
        try:
            return history.get(run_id)
        except KeyError:
            raise HTTPException(404,'Unknown investigation') from None

    def worker(run_id,request,context,directory):
        history.set_status(run_id,'running')
        try:
            if runner:
                report=runner(run_id,request,context,directory)
            else:
                trace=Trace(directory,quiet=True)
                key=os.getenv('GROQ_API_KEY','').strip()
                model=request.model
                llm=GroqLLM(key,model,trace,float(os.getenv('VULNBRIEF_MIN_REQUEST_INTERVAL','25')))
                context_path=None
                if context:
                    context_path=storage/'inputs'/f'{run_id}.json'
                    context_path.write_text(json.dumps(context),encoding='utf-8')
                tools=ToolKit(context_path,request.inject_failure)
                try:
                    report=Investigator(llm,tools,trace).run(request.goal)
                finally:
                    tools.close();llm.close()
            history.save(report,directory,context)
        except Exception as exc:
            # Never return provider exception bodies, credentials or local paths.
            history.set_status(run_id,'failed',f'Local investigation failed ({type(exc).__name__}); inspect configuration and saved events')

    def launch(request):
        if not runner and not os.getenv('GROQ_API_KEY','').strip():
            raise HTTPException(400,'Configure GROQ_API_KEY in the project .env first')
        if not request.goal.strip():
            raise HTTPException(422,'Enter an investigation goal')
        context=None
        if request.inventory_text.strip():
            # Parse a temporary explicitly selected input, never a client-supplied path.
            temporary=storage/'inputs'/f'validate-{uuid4().hex}.{request.inventory_format}'
            try:
                temporary.write_text(request.inventory_text,encoding='utf-8')
                context=load_context(temporary)[0].model_dump()
            except (ValueError,OSError):
                raise HTTPException(422,'Inventory does not match the documented JSON/CSV schema') from None
            finally:
                temporary.unlink(missing_ok=True)
        with launch_lock:
            if len([r for r in history.list() if r['status'] in {'queued','running'}])>=3:
                raise HTTPException(409,'Three investigations are already queued or running')
            run_id=uuid4().hex[:16]
            directory=storage/'runs'/run_id
            history.create(run_id,request.goal,directory,context,request.model)
            executor.submit(worker,run_id,request,context,directory)
        return {'run_id':run_id,'status':'queued'}

    @app.get('/api/config')
    def config():
        return {'model':os.getenv('VULNBRIEF_MODEL','openai/gpt-oss-120b'),
                'key_configured':bool(os.getenv('GROQ_API_KEY','').strip()),'version':'0.2.0',
                'supported_vendor':'PAN-OS advisory/version pilot; other products remain unverified'}

    @app.get('/api/example')
    def example():
        path=project/'examples'/'asset_inventory.csv'
        if not path.exists():
            raise HTTPException(404,'Example inventory not found in this project directory')
        return {'text':path.read_text(encoding='utf-8'),'format':'csv'}

    @app.get('/api/runs')
    def runs():
        return history.list()

    @app.post('/api/runs',status_code=202)
    def start(request:StartRun):
        return launch(request)

    @app.get('/api/runs/{run_id}')
    def detail(run_id:str):
        data=existing(run_id)
        data.pop('directory')
        return data

    @app.post('/api/runs/{run_id}/rerun',status_code=202)
    def rerun(run_id:str,request:StartRun):
        existing(run_id)
        return launch(request)

    @app.get('/api/runs/{run_id}/events')
    def events(run_id:str,after:int=0):
        data=existing(run_id)
        path=Path(data['directory'])/'events.jsonl'
        result=[]
        if path.exists():
            for line in path.read_text(encoding='utf-8').splitlines():
                try:
                    event=json.loads(line)
                    if event['sequence']>after:
                        result.append(event)
                except ValueError:
                    continue  # Writer may currently be appending the last line.
        return result

    @app.get('/api/runs/{run_id}/download/{kind}')
    def download(run_id:str,kind:str):
        names={'report':'report.md','json':'report.json','trace':'transcript.md','events':'events.jsonl'}
        if kind not in names:
            raise HTTPException(404,'Unknown artifact')
        data=existing(run_id);path=Path(data['directory'])/names[kind]
        if not path.is_file():
            raise HTTPException(404,'Artifact is not ready')
        return FileResponse(path,filename=f'{run_id}-{names[kind]}')

    @app.get('/api/compare')
    def compare(before:str,after:str):
        a,b=existing(before)['report'],existing(after)['report']
        if not a or not b:
            raise HTTPException(409,'Both investigations need completed report artifacts')
        return compare_reports(a,b)

    @app.get('/api/tasks')
    def tasks(run_id:str|None=None):
        return history.tasks(run_id)

    @app.patch('/api/tasks/{task_id}')
    def review(task_id:str,request:TaskReview):
        try:
            return history.review_task(task_id,request.status,request.review_note,request.owner)
        except KeyError:
            raise HTTPException(404,'Unknown task') from None

    @app.get('/api/tasks-export')
    def export(run_id:str|None=None):
        fields=['task_id','run_id','cve_id','asset','owner','priority','action','applies_when','support','source_links','applicability','status','review_note']
        stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for task in history.tasks(run_id):
            row={k:json.dumps(task.get(k,[])) if k in {'support','source_links'} else str(task.get(k,'')) for k in fields}
            row={k:("'"+v if v.lstrip().startswith(('=','+','-','@')) else v) for k,v in row.items()}
            writer.writerow(row)
        return Response(stream.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="vulnbrief-task-drafts.csv"'})

    app.mount('/',StaticFiles(directory=Path(__file__).parent/'web',html=True),name='workbench')
    return app
