import importlib

import os
import time

from aios.hooks.syscall import send_request

from pyopenagi.utils.chat_template import Query

from pyopenagi.utils.logger import AgentLogger

import json

class AcademicAgent:
    def __init__(self, agent_name, task_input, log_mode: str):
        self.agent_name = agent_name
        self.config = self.load_config()
        self.tool_names = self.config["tools"]
        
        self.plan_max_fail_times = 3
        self.tool_call_max_fail_times = 3

        # self.agent_process_factory = agent_process_factory

        self.tool_list = dict()
        self.tools = []
        self.tool_info = (
            []
        )  # simplified information of the tool: {"name": "xxx", "description": "xxx"}

        self.load_tools(self.tool_names)

        self.start_time = None
        self.end_time = None
        self.request_waiting_times: list = []
        self.request_turnaround_times: list = []
        self.task_input = task_input
        self.messages = []
        self.workflow_mode = "manual"  # (mannual, automatic)
        self.rounds = 0

        self.log_mode = log_mode
        self.logger = self.setup_logger()

        self.set_status("active")
        self.set_created_time(time.time())

    def check_path(self, tool_calls):
        script_path = os.path.abspath(__file__)
        save_dir = os.path.join(
            os.path.dirname(script_path), "output"
        )  # modify the customized output path for saving outputs
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        for tool_call in tool_calls:
            try:
                for k in tool_call["parameters"]:
                    if "path" in k:
                        path = tool_call["parameters"][k]
                        if not path.startswith(save_dir):
                            tool_call["parameters"][k] = os.path.join(
                                save_dir, os.path.basename(path)
                            )
            except Exception:
                continue
        return tool_calls

    def build_system_instruction(self):
        prefix = "".join(
            [
                "".join(self.config["description"])
            ]
        )

        plan_instruction = "".join(
            [
                f'You are given the available tools from the tool list: {json.dumps(self.tool_info)} to help you solve problems. ',
                'Generate a plan with comprehensive yet minimal steps to fulfill the task. ',
                'The plan must follow the json format as below: ',
                '[',
                '{"message": "message_value1","tool_use": [tool_name1, tool_name2,...]}',
                '{"message": "message_value2", "tool_use": [tool_name1, tool_name2,...]}',
                '...',
                ']',
                'In each step of the planned plan, identify tools to use and recognize no tool is necessary. ',
                'Followings are some plan examples. ',
                '['
                '[',
                '{"message": "gather information from arxiv. ", "tool_use": ["arxiv"]},',
                '{"message", "write a summarization based on the gathered information. ", "tool_use": []}',
                '];',
                '[',
                '{"message": "gather information from arxiv. ", "tool_use": ["arxiv"]},',
                '{"message", "understand the current methods and propose ideas that can improve ", "tool_use": []}',
                ']',
                ']'
            ]
        )

        if self.workflow_mode == "manual":
            self.messages.append(
                {"role": "system", "content": prefix}
            )

        else:
            assert self.workflow_mode == "automatic"
            self.messages.append(
                {"role": "system", "content": prefix}
            )
            self.messages.append(
                {"role": "user", "content": plan_instruction}
            )
            
    def automatic_workflow(self):
        for i in range(self.plan_max_fail_times):
            response, start_times, end_times, waiting_times, turnaround_times = send_request(
                agent_name = self.agent_name,
                query=Query(
                    messages=self.messages, tools=None, message_return_type="json"
                )
            )

            if self.rounds == 0:
                self.set_start_time(start_times[0])

            self.request_waiting_times.extend(waiting_times)
            self.request_turnaround_times.extend(turnaround_times)

            workflow = self.check_workflow(response.response_message)

            self.rounds += 1

            if workflow:
                return workflow

            else:
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": f"Fail {i+1} times to generate a valid plan. I need to regenerate a plan",
                    }
                )
        return None
    
    def manual_workflow(self):
        workflow = [
            {
                "action_type": "message_llm",
                "action": "Search for relevant papers",
                "tool_use": ["arxiv"],
            },
            {
                "action_type": "message_llm",
                "action": "Provide responses based on the user's query",
                "tool_use": [],
            }
        ]
        return workflow

    def call_tools(self, tool_calls):
        # self.logger.log(f"***** It starts to call external tools *****\n", level="info")
        success = True
        actions = []
        observations = []

        # print(tool_calls)
        for tool_call in tool_calls:
            # print(tool_call)
            function_name = tool_call["name"]
            function_to_call = self.tool_list[function_name]
            function_params = tool_call["parameters"]

            try:
                function_response = function_to_call.run(function_params)
                actions.append(f"I will call the {function_name} with the params as {function_params}")
                observations.append(f"The output of calling the {function_name} tool is: {function_response}")

            except Exception:
                actions.append("I fail to call any tools.")
                observations.append(f"The tool parameter {function_params} is invalid.")
                success = False

        return actions, observations, success
    
    def run(self):
        self.build_system_instruction()

        task_input = self.task_input

        self.messages.append({"role": "user", "content": task_input})
        self.logger.log(f"{task_input}\n", level="info")

        workflow = None

        if self.workflow_mode == "automatic":
            workflow = self.automatic_workflow()
        else:
            assert self.workflow_mode == "manual"
            workflow = self.manual_workflow()

        self.messages = self.messages[:1]  # clear long context

        self.messages.append(
            {
                "role": "user",
                "content": f"[Thinking]: The workflow generated for the problem is {json.dumps(workflow)}. Follow the workflow to solve the problem step by step. ",
            }
        )

        # if workflow:
        #     self.logger.log(f"Generated workflow is: {workflow}\n", level="info")
        # else:
        #     self.logger.log(
        #         "Fail to generate a valid workflow. Invalid JSON?\n", level="info"
        #     )
        
        try:
            if workflow:
                final_result = ""

                for i, step in enumerate(workflow):
                    action_type = step["action_type"]
                    action = step["action"]
                    tool_use = step["tool_use"]

                    prompt = f"At step {i + 1}, you need to: {action}. "
                    self.messages.append({"role": "user", "content": prompt})
                    
                    if tool_use:
                        selected_tools = self.pre_select_tools(tool_use)

                    else:
                        selected_tools = None

                    (
                        response,
                        start_times,
                        end_times,
                        waiting_times,
                        turnaround_times,
                    ) = send_request(
                        agent_name=self.agent_name,
                        query=Query(
                            messages=self.messages,
                            tools=selected_tools,
                            action_type=action_type,
                        )
                    )

                    if self.rounds == 0:
                        self.set_start_time(start_times[0])

                    # execute action
                    response_message = response.response_message

                    tool_calls = response.tool_calls

                    self.request_waiting_times.extend(waiting_times)
                    self.request_turnaround_times.extend(turnaround_times)

                    if tool_calls:
                        for _ in range(self.plan_max_fail_times):
                            tool_calls = self.check_path(tool_calls)
                            actions, observations, success = self.call_tools(
                                tool_calls=tool_calls
                            )

                            action_messages = "[Action]: " + ";".join(actions)
                            observation_messages = "[Observation]: " + ";".join(
                                observations
                            )

                            self.messages.append(
                                {
                                    "role": "assistant",
                                    "content": action_messages
                                    + ". "
                                    + observation_messages,
                                }
                            )
                            if success:
                                break
                    else:
                        thinkings = response_message
                        self.messages.append(
                            {"role": "assistant", "content": thinkings}
                        )

                    if i == len(workflow) - 1:
                        final_result = self.messages[-1]

                    step_result = self.messages[-1]["content"]
                    self.logger.log(f"At step {i + 1}, {step_result}\n", level="info")

                    self.rounds += 1

                self.set_status("done")
                self.set_end_time(time=time.time())

                return {
                    "agent_name": self.agent_name,
                    "result": final_result,
                    "rounds": self.rounds,
                    "agent_waiting_time": self.start_time - self.created_time,
                    "agent_turnaround_time": self.end_time - self.created_time,
                    "request_waiting_times": self.request_waiting_times,
                    "request_turnaround_times": self.request_turnaround_times,
                }

            else:
                return {
                    "agent_name": self.agent_name,
                    "result": "Failed to generate a valid workflow in the given times.",
                    "rounds": self.rounds,
                    "agent_waiting_time": None,
                    "agent_turnaround_time": None,
                    "request_waiting_times": self.request_waiting_times,
                    "request_turnaround_times": self.request_turnaround_times,
                }
        except Exception as e:
            print(e)
            return {}
        
    def snake_to_camel(self, snake_str):
        components = snake_str.split("_")
        return "".join(x.title() for x in components)

    def load_tools(self, tool_names):
        if tool_names == "None":
            return

        for tool_name in tool_names:
            org, name = tool_name.split("/")
            module_name = ".".join(["pyopenagi", "tools", org, name])
            class_name = self.snake_to_camel(name)

            tool_module = importlib.import_module(module_name)
            tool_class = getattr(tool_module, class_name)

            self.tool_list[name] = tool_class()
            tool_format = tool_class().get_tool_call_format()
            self.tools.append(tool_format)
            self.tool_info.append(
                {
                    "name": tool_format["function"]["name"],
                    "description": tool_format["function"]["description"],
                }
            )

    def pre_select_tools(self, tool_names):
        pre_selected_tools = []
        for tool_name in tool_names:
            for tool in self.tools:
                if tool["function"]["name"] == tool_name:
                    pre_selected_tools.append(tool)
                    break

        return pre_selected_tools

    def setup_logger(self):
        logger = AgentLogger(self.agent_name, self.log_mode)
        return logger

    def load_config(self):
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        config_file = os.path.join(script_dir, "config.json")
        with open(config_file, "r") as f:
            config = json.load(f)
            return config

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

    def set_start_time(self, time):
        self.start_time = time

    def get_start_time(self):
        return self.start_time

    def set_end_time(self, time):
        self.end_time = time

    def get_end_time(self):
        return self.end_time