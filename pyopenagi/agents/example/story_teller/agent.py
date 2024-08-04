from ...react_agent import ReactAgent

from ....utils.chat_template import Query

import os

import time

import json
class StoryTeller(ReactAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 agent_process_factory,
                 log_mode: str
        ):
        ReactAgent.__init__(self, agent_name, task_input, agent_process_factory, log_mode)
        # self.workflow_mode = "automatic"
        self.workflow_mode = "manual"

    def manual_workflow(self):
        workflow = [
            {
                "message": "Determine the story genre and theme based on user input.",
                "tool_use": []
            },
            {
                "message": "Generate initial story plot and characters.",
                "tool_use": []
            },
            {
                "message": "Create visual representations for the main character.",
                "tool_use": ["text_to_image"]
            },
            {
                "message": "Write descriptive text for each image and analyze each image",
                "tool_use": ["doc_question_answering"]
            },
            {
                "message": "Incorporate it into the story narrative.",
                "tool_use": []
            }
        ]
        return workflow

    def check_path(self, tool_calls):
        script_path = os.path.abspath(__file__)
        save_dir = os.path.join(os.path.dirname(script_path), "output") # modify the customized output path for saving outputs
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        for tool_call in tool_calls:
            if "path" in tool_call["parameters"]:
                path = tool_call["parameters"]["path"]
                if not path.startswith(save_dir):
                    tool_call["parameters"]["path"] = os.path.join(save_dir, os.path.basename(path))
        return tool_calls

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
                        tool_calls = self.check_path(tool_calls)
                        # print(tool_calls)
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
                    final_result = self.messages[-1]["content"]

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
