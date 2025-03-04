# This manages restoring and snapshotting the context.
# The file is used in the BaseLLM class and the RRScheduler class.

from aios.context.base import BaseContextManager

from litellm import completion

from openai import OpenAI

import time

class SimpleContextManager(BaseContextManager):
    def __init__(self):
        BaseContextManager.__init__(self)
        self.context_dict = {}

    def start(self):
        pass

    def save_context(self, model_name,model, messages, tools, temperature, pid, time_limit):
        if isinstance(model, str):
            response = completion(
                model=model,
                messages=messages,
                # tools=tools,
                temperature=temperature,
                stream=True
            )
            start_time = time.time()
            completed_response = ""
            
            finished = True
            
            for part in response:
                completed_response += part.choices[0].delta.content or ""
                if time.time() - start_time > time_limit:
                    if part.choices[0].finish_reason is None:
                        finished = False
                    break
                
            self.context_dict[str(pid)] = completed_response
            return completed_response, finished
        
        elif isinstance(model, OpenAI):
            completed_response = model.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                stream=True
            )
            start_time = time.time()
            completed_response = ""
            
            finished = True
            
            for part in response:
                completed_response += part.choices[0].delta.content or ""
                if time.time() - start_time > time_limit:
                    if part.choices[0].finish_reason is None:
                        finished = False
                    break
            self.context_dict[str(pid)] = completed_response
            return completed_response, finished

    def load_context(self, pid, model, tokenizer=None):
        context = self.check_context(pid)
        
        if context is None:
            return ""
        
        # Add type checking
        if isinstance(context, str) and not isinstance(model, str):
            raise TypeError("When context is string type, model must also be string type")
        if not isinstance(context, str) and isinstance(model, str):
            raise TypeError("When model is string type, context must also be string type")
        
        if isinstance(model, str):
            return context
        elif isinstance(model, OpenAI):
            return context
        else:
            # For local models that return tensors, decode using tokenizer
            if tokenizer:
                return tokenizer.decode(context)
            return context

    def check_context(self, pid):
        return self.context_dict.get(str(pid), None)

    def clear_context(self, pid):
        self.context_dict.pop(pid)
        return

    def stop(self):
        pass
