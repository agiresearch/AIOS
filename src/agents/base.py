import os

import json

from src.agents.agent_process import (
    AgentProcess,
    # AgentProcessQueue
)

from src.utils.global_param import (
    MAX_AID,
    aid_pool,
    # agent_pool,
)

import time

from threading import Thread

from datetime import datetime

class CustomizedThread(Thread):
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self):
        super().join()
        return self._return

class BaseAgent:
    def __init__(self, agent_name, task_input, llm, agent_process_queue):
        self.agent_name = agent_name
        self.config = self.load_config()
        self.prefix = self.config["description"]
        self.task_input = task_input
        self.llm = llm
        self.agent_process_queue = agent_process_queue

        aid = -1
        for id, used in enumerate(aid_pool):
            if used is False:
                aid = id
                aid_pool[id] = True
                break
                
        self.set_aid(aid)
        # time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.initialized_time = time.time()

        print(agent_name + " has been initialized.")
        # print(f"Initialized time: {self.initialized_time}")
    
        # self.memory_pool = SingleMemory()
        
        self.set_status("Active")
        self.set_created_time(time)
        
        
    def run(self):
        '''Execute each step to finish the task.'''
        pass

    def load_config(self):
        config_file = os.path.join(os.getcwd(), "src", "agents", "agent_config/{}.json".format(self.agent_name))
        with open(config_file, "r") as f:
            config = json.load(f)
            return config

    def send_request(self, process):
        pass
        # agent_process_queue.add(process)

    def get_response(self, prompt):
        agent_process = AgentProcess(self.agent_name, prompt)
        # args = [prompt]
        # task = self.agent_process_queue.submit(lambda p:self.llm.address_request(*p), args)
        self.agent_process_queue.put(agent_process)
        thread = CustomizedThread(target=self.listen, args=(agent_process,))
        thread.start()
        # print(result)
        return thread.join()

    def listen(self, agent_process):
        while agent_process.get_response() is None:
            time.sleep(0.2)
        
        return agent_process.get_response()
    

    def check_tool_use(self, prompt, tool_info, temperature=0.):
        prompt = f'You are allowed to use the following tools: \n\n```{tool_info}```\n\n' \
                f'Do you think the response ```{prompt}``` calls any tool?\n' \
                f'Only answer "Yes" or "No".'
        while True:
            # args = [prompt, temperature]
            # task = self.agent_process_queue.submit(lambda p:self.llm.address_request(*p), args)
            # response = task.result()
            response = self.get_response()
            temperature += .5
            print(f'Tool use check: {response}')
            if 'yes' in response.lower():
                return True
            if 'no' in response.lower():
                return False
            print(f'Temperature: {temperature}')
            if temperature > 2:
                break
        print('No valid format output when calling "Tool use check".')
        # exit(1)

    def get_prompt(self, tool_info, flow_ptr, task_description, cur_progress):
        progress_str = '\n'.join(cur_progress)
        prompt = f'{tool_info}\n\nCurrent Progress:\n{progress_str}\n\nTask description: {task_description}\n\n' \
                f'Question: {flow_ptr.get_instruction()}\n\nOnly answer the current instruction and do not be verbose.'
        return prompt

    def get_tool_arg(self, prompt, tool_info, selected_tool):
        prompt = f'{tool_info}\n\n' \
                f'You attempt to use the tool ```{selected_tool}```. ' \
                f'What is the input argument to call tool for this step: ```{prompt}```? ' \
                f'Respond "None" if no arguments are needed for this tool. Separate by comma if there are multiple arguments. Do not be verbose!'
        # args = [prompt]
        # task = self.agent_process_queue.submit(lambda p:self.llm.address_request(*p), args)
        # response = task.result()
        response = self.get_response()
        print(f'Parameters: {response}')
        return response

    def check_tool_name(self, prompt, tool_list, temperature=0.):
        prompt = f'Choose the used tool of ```{prompt}``` from the following options:\n'
        for i, key in enumerate(tool_list):
            prompt += f'{i + 1}: {key}.\n'
        prompt += "Your answer should be only an number, referring to the desired choice. Don't be verbose!"
        while True:
            # args = [prompt, temperature]
            # task = self.agent_process_queue.submit(lambda p:self.llm.address_request(*p), args)
            # response = task.result()
            response = self.get_response()
            temperature += .5
            if response.isdigit() and 1 <= int(response) <= len(tool_list):
                response = int(response)
                break
            print(f'Temperature: {temperature}')
            if temperature > 2:
                # logging.info('No valid format output when calling "Tool name select".')
                exit(1)
        # logging.info(f'{response}, {tool_list[response - 1]}')
        return tool_list[response - 1]
    
    def check_branch(self, prompt, flow_ptr, temperature=0.):
        possible_keys = list(flow_ptr.branch.keys())
        prompt = f'Choose the closest representation of ```{prompt}``` from the following options:\n'
        for i, key in enumerate(possible_keys):
            prompt += f'{i + 1}: {key}.\n'
        prompt += "Your answer should be only an number, referring to the desired choice. Don't be verbose!"
        while True:
            # args = [prompt, temperature]
            # task = self.agent_process_queue.submit(lambda p:self.llm.address_request(*p), args)
            # response = task.result()
            response = self.get_response()
            temperature += .5
            if response.isdigit() and 1 <= int(response) <= len(possible_keys):
                response = int(response)
                break
            print(f'Temperature: {temperature}')
            if temperature > 2:
                print('No valid format output when calling "Check Branch".')
                exit(1)
        print(f'{response}, {possible_keys[response - 1]}')
        return possible_keys[response - 1]

    def set_aid(self, aid):
        self.aid = aid

    def get_aid(self):
        return self.aid

    def get_agent_name(self):
        return self.agent_name

    def set_status(self, status):

        """
        Status type: Waiting, Running, Done, Inactive
        """
        self.status = status

    def get_status(self):
        return self.status

    def set_created_time(self, time):
        self.created_time = time

    def get_created_time(self):
        return self.created_time

    def parse_result(self, prompt):
        pass
        