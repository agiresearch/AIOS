
from .base_agent import BaseAgent

import time

from ..utils.chat_template import Query

import json

class ReactAgent(BaseAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 agent_process_factory,
                 log_mode: str
        ):
        BaseAgent.__init__(
            self,
            agent_name,
            task_input,
            agent_process_factory,
            log_mode
        )

        self.plan_max_fail_times = 3
        self.tool_call_max_fail_times = 3

    def build_system_instruction(self):
        prefix = "".join(
            [
                "".join(self.config["description"])
            ]
        )

        plan_instruction = "".join(
            [
                f'You are given the available tools from the tool list: {json.dumps(self.tool_info)} to help you solve problems. ',
                'Generate a plan of steps you need to take. ',
                'The plan must follow the json format as: ',
                '[',
                '{"message": "message_value1","tool_use": [tool_name1, tool_name2,...]}',
                '{"message": "message_value2", "tool_use": [tool_name1, tool_name2,...]}',
                '...',
                ']',
                'In each step of the planned workflow, you must select the most related tool to use',
                'Followings are some plan examples:',
                '[',
                '{"message": "gather information from arxiv. ", "tool_use": ["arxiv"]},',
                '{"message", "write a summarization based on the gathered information. ", "tool_use": []}',
                '];',
                '[',
                '{"message": "identify the tool that you need to call to obtain information. ", "tool_use": ["imdb_top_movies", "imdb_top_series"]},',
                '{"message", "give recommendations for the user based on the information. ", "tool_use": []}',
                '];',
            ]
        )

        if self.workflow_mode == "manual":
            self.messages.append(
                {"role": "system", "content": prefix}
            )

        else:
            assert self.workflow_mode == "automatic"
            self.messages.append(
                {"role": "system", "content": prefix + plan_instruction}
            )


    def automatic_workflow(self):
        return super().automatic_workflow()

    def manual_workflow(self):
        pass

    def call_tools(self, tool_calls):
        # self.logger.log(f"***** It starts to call external tools *****\n", level="info")
        success = True
        actions = []
        observations = []
        for tool_call in tool_calls:
            function_name = tool_call["name"]
            function_to_call = self.tool_list[function_name]
            function_params = tool_call["parameters"]

            try:
                function_response = function_to_call.run(function_params)
                actions.append(f"I will call the {function_name} with the params as {function_params}")
                observations.append(f"The knowledge I get from {function_name} is: {function_response}")

            except Exception:
                actions.append("I fail to call any tools.")
                observations.append(f"The tool parameter {function_params} is invalid.")
                success = False

        return actions, observations, success

    def run(self):
        self.build_system_instruction()

        task_input = self.task_input

        self.messages.append(
            {"role": "user", "content": task_input}
        )
        self.logger.log(f"{task_input}\n", level="info")

        workflow = None

        if self.workflow_mode == "automatic":
            workflow = self.automatic_workflow()
        else:
            assert self.workflow_mode == "manual"
            workflow = self.manual_workflow()

        self.messages.append(
            {"role": "assistant", "content": f"[Thinking]: The workflow generated for the problem is {json.dumps(workflow)}"}
        )

        self.messages.append(
            {"role": "user", "content": "[Thinking]: Follow the workflow to solve the problem step by step. "}
        )

        self.logger.log(f"Generated workflow is: {workflow}\n", level="info")

        if workflow:
            final_result = ""

            for i, step in enumerate(workflow):
                message = step["message"]
                tool_use = step["tool_use"]

                # print(f"message: {message}")
                # print(f"tool use: {tool_use}")

                prompt = f"At step {i + 1}, you need to {message}. "
                self.messages.append({
                    "role": "user",
                    "content": prompt
                })
                if tool_use:
                    selected_tools = self.pre_select_tools(tool_use)

                else:
                    selected_tools = None

                response, start_times, end_times, waiting_times, turnaround_times = self.get_response(
                    query = Query(
                        messages = self.messages,
                        tools = selected_tools
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
                        actions, observations, success = self.call_tools(tool_calls=tool_calls)

                        action_messages = "[Action]: " + ";".join(actions)
                        observation_messages = "[Observation]: " + ";".join(observations)

                        self.messages.append(
                            {
                                "role": "assistant",
                                "content": action_messages + ". " + observation_messages
                            }
                        )
                        if success:
                            break
                else:
                    thinkings = response_message
                    self.messages.append({
                        "role": "assistant",
                        "content": thinkings
                    })

                if i == len(workflow) - 1:
                    final_result = self.messages[-1]

                self.logger.log(f"At step {i + 1}, {self.messages[-1]}\n", level="info")

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
