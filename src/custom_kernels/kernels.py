from src.custom_kernels.base import BaseKernel
from src.custom_kernels.cache import Cache
from openai import OpenAI
import os
import threading

from src.memory.os.handler import MemoryHandler

class GPTKernel(BaseKernel):
    def __init__(self, name: str = 'gpt-3.5-turbo'):
        self.cache = Cache()
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model_name = name
        self.__flag: list[str, str] = ['PLAY', 'PLAY']
        self.__execute_thread = None  

    def execute(self, phrase: str, done_event: threading.Event):
        

        def execute_helper():
            self.cache.add_user(phrase)

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {'role': 'user', 'content': phrase}
                ],
                temperature=0.3,
                stream=True  
            )

            for chunk in response:
                if self.__flag[0] == 'PLAY' and self.__flag[1] == 'PAUSE':
                    self.cache.toggle()
                    self.cache.stream('$^@', show_breaks=True)
                    self.__flag[0] = 'PAUSE'


                if self.__flag[1] == 'PLAY' and self.__flag[0] == 'PAUSE':
                    self.cache.toggle()
                    self.cache.stream('$^@', show_breaks=True)
                    self.__flag[0] = 'PLAY'
                
                if chunk.choices[0].delta.content == None:
                    self.cache.stream('$^@', show_breaks=True)
                else:
                    self.cache.stream(chunk.choices[0].delta.content, show_breaks=True)

            print(self.cache.history[1].content)
            done_event.set()  

        self.__execute_thread = threading.Thread(target=execute_helper)
        self.__execute_thread.start()

    def play(self):
        self.__flag[0] = 'PAUSE'
        self.__flag[1] = 'PLAY'
    
    def pause(self):
        self.__flag[0] = 'PLAY'
        self.__flag[1] = 'PAUSE'
    
    def end(self):
        self.__flag = 'END'
