import importlib
import os
import time
import json
from typing import Optional, List, Dict, Any
from aios.hooks.request import send_request
from pyopenagi.utils.chat_template import Query
from pyopenagi.utils.logger import AgentLogger

try:
    from tqdm.autonotebook import tqdm
except ImportError:
    from tqdm import tqdm
    
class SeeActAgent:
    def __init__(self, agent_name: str, task_input: str, log_mode: str):
        self.agent_name = agent_name
        self.config = self.load_config()
        self.tool_names = self.config.get("tools", [])
        
        self.plan_max_fail_times = 3
        self.tool_call_max_fail_times = 3

        self.tool_list = dict()
        self.tools = []
        self.tool_info = []

        # 修改日志配置
        self.log_mode = "console" if log_mode == "info" else log_mode
        self.logger = self.setup_logger()

        try:
            self.load_tools(self.tool_names)
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error loading tools: {str(e)}", "info")
            print(f"Error loading tools: {str(e)}")

        self.start_time = None
        self.end_time = None
        self.created_time = None
        self.request_waiting_times: list = []
        self.request_turnaround_times: list = []
        self.task_input = task_input
        self.messages = []
        self.workflow_mode = "manual"
        self.rounds = 0

        self.set_status("active")
        self.set_created_time(time.time())

    def setup_logger(self):
        """设置日志记录器"""
        try:
            # 直接使用正确的参数创建AgentLogger
            # AgentLogger期望的参数是 (logger_name, log_mode="console")
            return AgentLogger(
                logger_name=self.agent_name,  # 第一个参数是logger_name
                log_mode=self.log_mode        # 第二个参数是log_mode
            )
        except Exception as e:
            print(f"Failed to setup logger: {str(e)}")
            # 返回None而不是抛出异常，这样agent还能继续运行
            return None


    # 添加一个简单的后备日志记录器
    class SimpleLogger:
        def log(self, content, level="info"):
            print(f"[{level.upper()}] {content}")


    def load_tools(self, tool_names: List[str]) -> None:
        """加载工具
        Args:
            tool_names: 工具名称列表，格式如 ['web/browser', 'file/downloader']
        """
        if not tool_names:
            self.logger.log("No tools to load", level="warning")
            return

        try:
            for tool_name in tool_names:
                if not tool_name or '/' not in tool_name:
                    self.logger.log(f"Invalid tool name format: {tool_name}", level="warning")
                    continue

                # 解析工具名称
                org, name = tool_name.split('/')
                if not org or not name:
                    self.logger.log(f"Invalid tool name: {tool_name}", level="warning")
                    continue

                # 构建模块路径
                module_name = f"pyopenagi.tools.{org}.{name}"
                class_name = self.snake_to_camel(name)

                try:
                    # 导入模块
                    tool_module = importlib.import_module(module_name)
                    tool_class = getattr(tool_module, class_name)

                    # 实例化工具
                    tool_instance = tool_class()
                    self.tool_list[name] = tool_instance

                    # 获取工具格式
                    tool_format = tool_instance.get_tool_call_format()
                    self.tools.append(tool_format)
                    self.tool_info.append({
                        "name": tool_format["function"]["name"],
                        "description": tool_format["function"]["description"]
                    })
                    
                    self.logger.log(f"Successfully loaded tool: {tool_name}", level="info")
                except ImportError as e:
                    self.logger.log(f"Failed to import tool {tool_name}: {str(e)}", level="error")
                except Exception as e:
                    self.logger.log(f"Error loading tool {tool_name}: {str(e)}", level="error")

        except Exception as e:
            self.logger.log(f"Error in load_tools: {str(e)}", level="error")
            raise

    def check_workflow(self, workflow_str: str) -> Optional[List[Dict]]:
        """检查工作流格式是否正确"""
        try:
            workflow = json.loads(workflow_str)
            if not isinstance(workflow, list):
                return None
            
            for step in workflow:
                if not isinstance(step, dict):
                    return None
                if "message" not in step or "tool_use" not in step:
                    return None
                if not isinstance(step["tool_use"], list):
                    return None
            
            return workflow
        except:
            return None

    def check_path(self, tool_calls):
        script_path = os.path.abspath(__file__)
        save_dir = os.path.join(os.path.dirname(script_path), "output")
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
        prefix = "".join(self.config["description"])

        plan_instruction = "".join([
            f'You are given the available tools from the tool list: {json.dumps(self.tool_info)} to help you solve problems. ',
            'Generate a plan with comprehensive yet minimal steps to fulfill the task. ',
            'The plan must follow the json format as below: ',
            '[',
            '{"message": "message_value1","tool_use": [tool_name1, tool_name2,...]}',
            '{"message": "message_value2", "tool_use": [tool_name1, tool_name2,...]}',
            '...',
            ']'
        ])

        if self.workflow_mode == "manual":
            self.messages.append({"role": "system", "content": prefix})
        else:
            self.messages.append({"role": "system", "content": prefix})
            self.messages.append({"role": "user", "content": plan_instruction})

    def automatic_workflow(self):
        for i in range(self.plan_max_fail_times):
            response, start_times, end_times, waiting_times, turnaround_times = send_request(
                agent_name=self.agent_name,
                query=Query(
                    messages=self.messages,
                    tools=None,
                    message_return_type="json"
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
                self.messages.append({
                    "role": "assistant",
                    "content": f"Fail {i+1} times to generate a valid plan. I need to regenerate a plan"
                })
        return None
    def manual_workflow(self):
        workflow = [
            {
                "action_type": "message_llm",
                "action": "Use web browser to search and navigate to the paper page",
                "tool_use": ["browser"]    # 使用 web browser 来搜索和浏览
            },
            {
                "action_type": "message_llm",
                "action": "Once found the paper, download the PDF",
                "tool_use": ["downloader"]  # 使用 downloader 来下载 PDF
            }
        ]
        return workflow

    def call_tools(self, tool_calls):
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
                observations.append(f"The output of calling the {function_name} tool is: {function_response}")
            except Exception:
                actions.append("I fail to call any tools.")
                observations.append(f"The tool parameter {function_params} is invalid.")
                success = False

        return actions, observations, success

    def run(self):
        try:
            self.build_system_instruction()
            task_input = self.task_input
            self.messages.append({"role": "user", "content": task_input})
            
            if self.logger:
                try:
                    self.logger.log(f"{task_input}\n", level="info")
                except Exception as e:
                    print(f"Logging failed: {str(e)}")
            else:
                print(f"[{self.agent_name}] {task_input}")

            workflow = None
            if self.workflow_mode == "automatic":
                workflow = self.automatic_workflow()
            else:
                workflow = self.manual_workflow()

            self.messages = self.messages[:1]

            self.messages.append({
                "role": "user",
                "content": f"[Thinking]: The workflow generated for the problem is {json.dumps(workflow)}. Follow the workflow to solve the problem step by step. "
            })

            if workflow:
                final_result = ""
                for i, step in enumerate(workflow):
                    action_type = step["action_type"]
                    action = step["action"]
                    tool_use = step["tool_use"]

                    prompt = f"At step {i + 1}, you need to: {action}. "
                    self.messages.append({"role": "user", "content": prompt})

                    selected_tools = self.pre_select_tools(tool_use) if tool_use else None

                    response, start_times, end_times, waiting_times, turnaround_times = send_request(
                        agent_name=self.agent_name,
                        query=Query(
                            messages=self.messages,
                            tools=selected_tools,
                            action_type=action_type
                        )
                    )

                    if self.rounds == 0:
                        self.set_start_time(start_times[0])

                    response_message = response.response_message
                    tool_calls = response.tool_calls

                    self.request_waiting_times.extend(waiting_times)
                    self.request_turnaround_times.extend(turnaround_times)

                    if tool_calls:
                        for _ in range(self.tool_call_max_fail_times):
                            tool_calls = self.check_path(tool_calls)
                            actions, observations, success = self.call_tools(tool_calls)

                            action_messages = "[Action]: " + ";".join(actions)
                            observation_messages = "[Observation]: " + ";".join(observations)

                            self.messages.append({
                                "role": "assistant",
                                "content": action_messages + ". " + observation_messages
                            })
                            if success:
                                break
                    else:
                        self.messages.append({
                            "role": "assistant",
                            "content": response_message
                        })

                    if i == len(workflow) - 1:
                        final_result = self.messages[-1]

                    step_result = self.messages[-1]["content"]
                    if self.logger:
                        self.logger.log(f"At step {i + 1}, {step_result}\n", level="info")

                    self.rounds += 1

                self.set_status("done")
                self.set_end_time(time.time())

                return {
                    "agent_name": self.agent_name,
                    "result": final_result,
                    "rounds": self.rounds,
                    "agent_waiting_time": self.start_time - self.created_time,
                    "agent_turnaround_time": self.end_time - self.created_time,
                    "request_waiting_times": self.request_waiting_times,
                    "request_turnaround_times": self.request_turnaround_times
                }
            else:
                return {
                    "agent_name": self.agent_name,
                    "result": "Failed to generate a valid workflow in the given times.",
                    "rounds": self.rounds,
                    "agent_waiting_time": None,
                    "agent_turnaround_time": None,
                    "request_waiting_times": self.request_waiting_times,
                    "request_turnaround_times": self.request_turnaround_times
                }

        except Exception as e:
            if self.logger:
                self.logger.log(f"Error in run method: {str(e)}", "info")
            print(f"Error in run method: {str(e)}")
            return {}
        
        
    def snake_to_camel(self, snake_str):
        components = snake_str.split("_")
        return "".join(x.title() for x in components)

    def pre_select_tools(self, tool_names):
        pre_selected_tools = []
        for tool_name in tool_names:
            for tool in self.tools:
                if tool["function"]["name"] == tool_name:
                    pre_selected_tools.append(tool)
                    break
        return pre_selected_tools

    def load_config(self):
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        config_file = os.path.join(script_dir, "config.json")
        with open(config_file, "r") as f:
            return json.load(f)

    def set_aid(self, aid):
        self.aid = aid

    def get_aid(self):
        return self.aid

    def get_agent_name(self):
        return self.agent_name

    def set_status(self, status):
        """Status type: Waiting, Running, Done, Inactive"""
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