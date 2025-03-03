# This manages restoring and snapshotting the context.
# The file is used in the BaseLLM class and the RRScheduler class.

from aios.context.base import BaseContextManager

from litellm import completion

class SimpleContextManager(BaseContextManager):
    def __init__(self):
        BaseContextManager.__init__(self)
        self.context_dict = {}

    def start(self):
        pass

    def save_context(self, model, messages, temperature, pid, time_limit):
        if isinstance(model, str):
            response = completion(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=True
            )
            start_time = time.time()
            completed_response = ""
            
            for part in response:
                completed_response += part.choices[0].delta.content or ""
                if time.time() - start_time > time_limit:
                    break
                
            self.context_dict[str(pid)] = completed_response
            return completed_response

    def load_context(self, pid):
        return self.context_dict[str(pid)]

    def check_context(self, pid):
        # return os.path.exists(os.path.join(self.context_dir, f"process-{pid}.pt"))
        return str(pid) in self.context_dict.keys()

    def clear_context(self, pid):
        self.context_dict.pop(pid)
        return

    def stop(self):
        pass
