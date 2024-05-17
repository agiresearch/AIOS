from typing import Union

from src.core_os.meta import StepType
from src.core_os.memory import SessionMemory
from src.core_os.engines import GPTEngine

from src.core_os.agents.config import Agent

from pprint import pprint as print

class Step:
    def __init__(self, name: str, instruction: str, _type: StepType, _next: Union['Step', dict[str, 'Step'], None], parent: 'StepRouter'):
        self.name= name
        self.instruction = instruction
        self._type =  _type
        self.parent = parent
        self._next=_next
        


    def _resolve(self, name='gpt-3.5-turbo', guidelines="""
        You are a capable AI manager that controls the OS of a computer. You will be given a task, delimited by triple backticks \
        , and expected to complete it by outputting the name of an agent \
        along with the parameters needed. MAKE SURE TO GIVE ALL PARAMETERS OUTLINED.
                 
        You also be given a memory consisting of current information/data you have, delimited by triple hashtags, and a list of possible agents. \
        Finally, ensure to output the results in JSON format, like \
        
        {
            agent_name: name here,
            parameters: object where keys are function param names, and values are the values that should be passed in,
            memory_description: description of what the agent returns so that the description and result of agent can be saved to memory for future usage
        }
    """, instruct=''):
        response_engine = GPTEngine(name=name, system=guidelines)

        agent_info = '\n\n'.join([a.__str__() for a in self.parent.agents])
        
        query = f"""
            Task: ```{self.instruction}```

            Memory: ###{self.parent.memory.read_memory()}###

            Agent Information: {agent_info}
        """

        return response_engine.query(query, is_json=True)
        
         
class StepRouter:
    def __init__(self, start: Step | None, pool: set[Step], agents: list[Agent], memory: SessionMemory):
        self.start = start
        self.pool = pool
        self.agents = agents
        self.memory = memory
        self.temp_pool = dict()
        self.flag = False

    def add_step(self, step: dict):
        if step.get('type') == 'decision':
            _type = StepType.DECISION
        elif step.get('type') == 'process':
            _type = StepType.PROCESS
        else:
            _type = StepType.TERMINAL

        s = Step(name=step.get('name'), instruction=step.get('description'), _next=None, parent=self, _type=_type)

        self.pool.add(s)
        self.temp_pool[step.get('name')] = step

    def set_entry(self, step: dict):
        if step.get('type') == 'decision':
            _type = StepType.DECISION
        elif step.get('type') == 'process':
            _type = StepType.PROCESS
        else:
            _type = StepType.TERMINAL

        self.start = Step(name=step.get('name'), instruction=step.get('description'), _next=None, parent=self, _type=_type)
        self.temp_pool[step.get('name')] = step

    def _get_step_by_name(self, name: str):
         return next((obj for obj in (self.pool | {self.start}) if obj.name == name), None)

    def chain(self):
        for step in self.pool | {self.start}:
            if step._type == StepType.PROCESS:
                step._next = self._get_step_by_name(self.temp_pool[step.name].get('next_step'))
            elif step._type == StepType.DECISION:
                tmp = self.temp_pool[step.name].get('next_step')

                for i in tmp.keys():
                    tmp[i] = self._get_step_by_name(tmp[i])
                
                step._next = tmp

    def execute(self, log_tail=True):
        try:
            start = self.start._resolve()
        except:
            start = self.start._resolve()
        
        start_function = Agent.retrieve_agent(start.get('agent_name'))._call
        start_value = start_function(**start.get('parameters'))
        self.memory.add_memory(f'{start.get('memory_description')}: {start_value}')

        _next_ = self.start._next

        while True:
            try:
                _next = _next_._resolve()
            except:
                _next = _next_._resolve()
            
            next_function = Agent.retrieve_agent(_next.get('agent_name'))._call
            next_value = next_function(**_next.get('parameters'))
            self.memory.add_memory(f'{_next.get('memory_description')}: {next_value}')
            
            if _next_._type ==  StepType.PROCESS:
                _next_ = _next_._next
            elif _next_._type == StepType.DECISION:
                _next_ = _next_._next.get(str(next_value))
            else:
                break

            if log_tail:
                print(self.memory.memory[-1])

            if self.flag:
                break


    
