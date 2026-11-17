"""Run a bounded repeated-trial suite against actual Groq and live source APIs.

Does not replay stored reports, mock the model, or overwrite old output folders.
No live evaluation is triggered by unit tests or CI.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from dotenv import load_dotenv
from vulnbrief.agent import Investigator
from vulnbrief.evaluation import grade_trial, write_summary
from vulnbrief.llm import GroqLLM
from vulnbrief.models import utc_now
from vulnbrief.tools import ToolKit
from vulnbrief.trace import Trace

BASE=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cases',default='missing_record,unsupported_vendor')
    p.add_argument('--trials',type=int,default=2)
    p.add_argument('--model',choices=['openai/gpt-oss-20b','openai/gpt-oss-120b'],default='openai/gpt-oss-20b')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--max-total-tokens',type=int,default=80000)
    p.add_argument('--max-seconds',type=int,default=480)
    args=p.parse_args()
    if not 1<=args.trials<=3 or not 10<=args.max_seconds<=600 or args.max_total_tokens<=0:p.error('Invalid evaluation bounds')
    suite=json.loads((BASE/'examples/evaluation-suite.json').read_text(encoding='utf-8'))
    index={c['id']:c for c in suite['cases']}
    ids=args.cases.split(',')
    if len(set(ids))!=len(ids) or any(i not in index for i in ids):p.error('Unknown or duplicate case id')
    load_dotenv(BASE/'.env',override=False);key=os.getenv('GROQ_API_KEY','').strip()
    if not key:p.error('GROQ_API_KEY must be configured locally')
    args.output.mkdir(parents=True,exist_ok=False)
    runtime=['agent','llm','tools','inventory','vendor','models','report','trace']
    fingerprint=hashlib.sha256(b''.join((BASE/f'src/vulnbrief/{name}.py').read_bytes() for name in runtime)).hexdigest()
    doc={'created_at':utc_now(),'scope':suite['scope'],'model':args.model,'runtime_fingerprint':fingerprint,
         'planned_cases':ids,'planned_trials':len(ids)*args.trials,'max_total_tokens':args.max_total_tokens,
         'per_trial_bounds':{'seconds':args.max_seconds,'rounds':8,'data_tool_attempts':12},'trials':[], 'stop_reason':None}
    total=0
    for case_id in ids:
        case=index[case_id]
        for trial in range(1,args.trials+1):
            if total>=args.max_total_tokens:
                doc['stop_reason']='Token budget reached between trials; an individual trial can exceed the remaining estimate';break
            directory=args.output/f'{case_id}-{trial:02d}'
            context=None
            if case.get('context_file'):context=BASE/case['context_file']
            elif case.get('context'):
                context=args.output/f'{case_id}-context.json'
                context.write_text(json.dumps(case['context'],indent=2),encoding='utf-8')
            trace=Trace(directory,quiet=True)
            llm=GroqLLM(key,args.model,trace,float(os.getenv('VULNBRIEF_MIN_REQUEST_INTERVAL','25')))
            tools=ToolKit(context,case.get('fault',False));report=None;rejection=None
            started=time.monotonic()
            print(f'Starting actual live trial {case_id}/{trial}',flush=True)
            try:
                report=Investigator(llm,tools,trace,8,12,args.max_seconds).run(case['goal'])
            except ValueError as exc:
                rejection=str(exc);trace.emit('input_rejected',message=rejection)
            finally:
                tools.close();llm.close()
            metrics=(report or {}).get('metrics',{'llm_calls':llm.calls,'total_tokens':llm.tokens,'elapsed_seconds':round(time.monotonic()-started,2)})
            checks=grade_trial(case,report,trace.events,rejection,llm.calls)
            row={'case_id':case_id,'trial':trial,'directory':directory.name,'status':(report or {}).get('status','input_rejected'),
                 'checks':checks,'metrics':metrics,'manual_semantic_accuracy':'not_assessed'}
            doc['trials'].append(row);total+=metrics['total_tokens']
            reason=(report or {}).get('stop_reason') or ''
            if 'daily provider quota' in reason.lower():doc['stop_reason']='Daily provider quota exhausted; no remaining trials were represented as completed'
            write_summary(args.output,doc)
            print(json.dumps(row),flush=True)
            if doc['stop_reason']:break
            time.sleep(2)
        if doc['stop_reason']:break
    doc['total_observed_tokens']=total;doc['finished_at']=utc_now();write_summary(args.output,doc)
    print(f'Evaluation saved to {args.output.resolve()}',flush=True)


if __name__=='__main__':main()
