from ..base import BaseTool 
from time import sleep

class Transcriber(BaseTool):
    def __init__(self):
        """ big library, not everyone needs it installed """
        try:
            from RealtimeSTT import AudioToTextRecorder
        except ImportError:
            raise ImportError(
                "Please install RealtimeSTT: `pip install RealtimeSTT`"
            )
        
        # this is hardcoded for now
        self.recorder = AudioToTextRecorder(
                model="tiny.en",
        )

    def run(self, params: dict):
        duration = 5
        try:
            duration = int(params["duration"])
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted key in params for transcriber api. "
                "Please make sure it contain the key 'duration'"
            )

        self.record.start()
        sleep(duration)
        self.recorder.stop()
        return self.recorder.text() 

    def get_tool_call_format(self):
        tool_call_format = {
            "type": "function",
            "function": {
                "name": "transcriber",
                "description": "Transcribes audiio into text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "duration": {
                            "type": "string",
                            "description": "How long to record audio for in seconds",
                        },
                    },
                    "required": []
                }
            }
        }
        return tool_call_format
