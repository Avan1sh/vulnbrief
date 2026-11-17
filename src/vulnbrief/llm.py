"""Small Groq adapter. No private reasoning or provider error bodies enter traces."""
import time
import json

from groq import APIConnectionError, APIStatusError, APITimeoutError, Groq, RateLimitError


class ProviderFailure(Exception):
    pass


class GroqLLM:
    def __init__(self, api_key: str, model: str, trace, min_interval: float = 25):
        self.client = Groq(api_key=api_key, max_retries=0)
        self.model, self.trace, self.min_interval = model, trace, min_interval
        self.last_started = 0.0
        self.calls = 0
        self.tokens = 0
        self.last_usage = 0

    def close(self):
        self.client.close()

    def _request(self, messages, deadline, **options):
        rate_retries=0
        schema_retries=0
        for attempt in range(3):
            interval=max(self.min_interval,self.last_usage/6000*60)
            wait = max(0, interval - (time.monotonic() - self.last_started))
            if time.monotonic() + wait + 2 >= deadline:
                raise ProviderFailure("Run deadline reached while pacing LLM requests")
            if wait:
                time.sleep(wait)
            self.last_started = time.monotonic()
            self.calls += 1
            try:
                result = self.client.chat.completions.create(
                    model=self.model, messages=messages, temperature=0.1,
                    max_completion_tokens=2600, reasoning_effort="low",
                    timeout=min(40, max(1, deadline - time.monotonic())), **options)
                used = result.usage.total_tokens if result.usage else 0
                self.tokens += used
                self.last_usage=used
                self.trace.emit("llm_usage", model=self.model, call=self.calls, total_tokens=used)
                if result.choices[0].finish_reason == "length":
                    raise ProviderFailure("Model response reached the output limit; no partial JSON was accepted")
                return result.choices[0].message
            except RateLimitError as exc:
                try:
                    detail=str(exc.response.json().get('error',{}).get('message','')).lower()
                except ValueError:
                    detail=''
                daily=any(s in detail for s in ('tokens per day','tokens_per_day','(tpd)','requests per day','(rpd)'))
                self.trace.emit("provider_retry", code="daily_quota" if daily else "rate_limit", attempt=attempt + 1)
                if daily:
                    raise ProviderFailure("Daily provider quota exhausted for this model; choose another supported free model or retry after quota reset") from None
                try:
                    delay = min(60, max(1, float(exc.response.headers.get("retry-after", "30"))))
                except ValueError:
                    delay = 30
                if rate_retries>=1 or time.monotonic() + delay + 2 >= deadline:
                    raise ProviderFailure("Provider rate limit; retry later or reduce request volume") from None
                rate_retries+=1
                time.sleep(delay)
            except (APIConnectionError, APITimeoutError):
                raise ProviderFailure("LLM provider connection failed or timed out") from None
            except APIStatusError as exc:
                try:
                    code=exc.response.json().get('error',{}).get('code')
                except ValueError:
                    code=None
                if exc.status_code==400 and code in {'json_validate_failed','tool_use_failed'} and schema_retries==0:
                    schema_retries+=1
                    self.trace.emit('provider_schema_retry',code=code,attempt=1)
                    required=options.get('response_format',{}).get('json_schema',{}).get('schema',{}).get('required',[])
                    correction=('Return only a JSON object matching the supplied schema. Do not call functions. ' if options.get('response_format') else 'Use only the declared function names and arguments. ')
                    messages=messages+[{'role':'user','content':'Protocol correction: '+correction+
                        ('Required top-level fields: '+', '.join(required) if required else '')}]
                    continue
                suffix=f" ({code})" if code in {'json_validate_failed','tool_use_failed'} else ''
                raise ProviderFailure(f"LLM provider returned HTTP {exc.status_code}{suffix}; check account, model and quota") from None
        raise ProviderFailure("Provider request exhausted")

    def structured(self, messages, schema, deadline):
        messages=[dict(message) for message in messages]
        instruction='\nSTRUCTURED OUTPUT STAGE: do not call functions or tools. Return only a JSON object matching the supplied schema, including all required fields. Tool names in a plan are text, not calls.'
        if messages and messages[0]['role']=='system':
            messages[0]['content']+=instruction
        else:
            messages.insert(0,{'role':'system','content':instruction})
        if self.model=='openai/gpt-oss-20b':
            # Its endpoint intermittently rejected strict-schema generations in live
            # testing. JSON mode + the same local Pydantic contract exposes invalid
            # responses to the bounded report-repair path instead of losing them.
            instructions={'role':'user','content':'Return a JSON object matching this exact schema, including every required field. '+json.dumps(schema.model_json_schema())}
            message=self._request(messages+[instructions],deadline,response_format={'type':'json_object'})
            return schema.model_validate_json(message.content or '')
        message = self._request(messages, deadline, response_format={"type": "json_schema", "json_schema": {
            "name": schema.__name__, "strict": True, "schema": schema.model_json_schema()}})
        return schema.model_validate_json(message.content or "")

    def decide(self, messages, tools, deadline):
        message = self._request(messages, deadline, tools=tools, tool_choice="auto",
                                parallel_tool_calls=True)
        calls = [{"id": call.id, "type": "function", "function": {
            "name": call.function.name, "arguments": call.function.arguments}} for call in message.tool_calls or []]
        # Only public answer content and tool calls; never message.reasoning.
        # A text finish is a control signal, not a validated report. Discard its
        # unsolicited prose; reporting receives only the original source observations.
        content = (message.content or "") if calls else "Model ended tool selection; proceeding to structured report validation."
        return {"role": "assistant", "content": content, "tool_calls": calls}
