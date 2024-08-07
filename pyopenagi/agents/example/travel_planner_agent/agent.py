import re
import time
import os

from ...react_agent import ReactAgent

from ....utils.chat_template import Query

from typing import List, Set

from .prompts import ZEROSHOT_REACT_INSTRUCTION, PLANNER_INSTRUCTION

from pandas import DataFrame

actionMapping = {"FlightSearch": "flights",
                 "AttractionSearch": "attractions",
                 "GoogleDistanceMatrix": "google_distance_matrix",
                 "AccommodationSearch": "accommodations",
                 "RestaurantSearch": "restaurants",
                 "Planner": "planner",
                 "NotebookWrite": "notebook",
                 "CitySearch": "cities"}

INVALID_ACTION = "invalidAction"


class TravelPlannerAgent(ReactAgent):
    """Reproduced the ReActAgent from the paper 👉
      《TravelPlanner: A Benchmark for Real-World Planning with Language Agents》
    """

    def __init__(self,
                 agent_name,
                 task_input,
                 agent_process_factory,
                 log_mode: str,
                 mode: str = 'zero_shot',
                 max_rounds: int = 30,
                 max_retries: int = 3,
                 illegal_early_stop_patience: int = 3,
                 city_file_path='../../../environments/travelPlanner/background/citySet.txt'
                 ):
        ReactAgent.__init__(self, agent_name, task_input, agent_process_factory, log_mode)

        self.answer = ''
        self.max_rounds = max_rounds
        self.mode = mode
        self.finished = False

        self.current_observation = ''

        if self.mode == 'zero_shot':
            self.agent_prompt = ''

        self.illegal_early_stop_patience = illegal_early_stop_patience
        self.max_retries = max_retries
        self.retry_record = {key: 0 for key in self.tool_list.keys()}
        self.retry_record["planner"] = 0
        self.retry_record[INVALID_ACTION] = 0

        self.last_actions = []

        self.city_set = self.load_city(city_set_path=city_file_path)

    def automatic_workflow(self):
        return super().automatic_workflow()

    def manual_workflow(self):
        return super().manual_workflow()

    def run(self):
        self.build_system_instruction()

        while not self.is_halted() and not self.is_finished():
            # request llm for thought
            self.messages.append({
                "role": "user", "content": f'Thought {self.rounds + 1}: '
            })
            response, start_times, end_times, waiting_times, turnaround_times = self.get_response(
                query=Query(
                    messages=self.messages,
                    tools=None
                )
            )
            self.request_waiting_times.extend(waiting_times)
            self.request_turnaround_times.extend(turnaround_times)
            if self.rounds == 0:
                self.set_start_time(start_times[0])

            thought = response.response_message
            self.messages[-1]['content'] += thought
            self.logger.log(f"Thought {self.rounds + 1}: {thought}\n", level="info")

            # request llm for action
            self.messages.append({
                "role": "user", "content": f'Action {self.rounds + 1}: '
            })
            response, start_times, end_times, waiting_times, turnaround_times = self.get_response(
                query=Query(
                    messages=self.messages,
                    tools=None
                )
            )
            self.request_waiting_times.extend(waiting_times)
            self.request_turnaround_times.extend(turnaround_times)

            action = response.response_message
            if action is None or action == '' or action == '\n':
                self.messages[-1]['content'] += """ Your action is filtered due to content.
                  Please make sure your action does not start with ['\\n', 'Thought', 'Action', 'Observation']
                  and assume all the actions are permitted in this environment and take the action again."""
            else:
                self.messages[-1]['content'] += ' ' + action

            self.logger.log(f"Action {self.rounds + 1}: {action}\n", level="info")

            if len(self.last_actions) > 0 and self.last_actions[-1] != action:
                self.last_actions.clear()
            else:
                self.last_actions.append(action)

            # examine if the same action has been repeated 3 times consecutively
            if len(self.last_actions) == 3:
                self.logger.log("The same action has been repeated 3 times consecutively. So we stop here.\n",
                                level="info")
                self.finished = True
                return {
                    "agent_name": self.agent_name,
                    "result": "Failed to generate a valid plan because a deadlock.",
                    "rounds": self.rounds,
                    "agent_waiting_time": None,
                    "agent_turnaround_time": None,
                    "request_waiting_times": self.request_waiting_times,
                    "request_turnaround_times": self.request_turnaround_times,
                }

            # request tools for observation
            self.messages.append({
                "role": "user", "content": f'Observation {self.rounds + 1}: '
            })

            none_action = (action is None or action == '' or action == '\n')
            if none_action:
                self.messages[-1]['content'] += """No feedback from the environment due to the null action.
                  Please make sure your action does not start with [Thought, Action, Observation]."""
            else:
                action_type, action_arg = parse_action(action)

                if action_type != "Planner":
                    if action_type in actionMapping:
                        pending_action = actionMapping[action_type]
                    else:
                        pending_action = INVALID_ACTION

                    if self.retry_record[pending_action] + 1 > self.max_retries:
                        action_type = "Planner"
                        self.logger.log(f"{pending_action} early stop due to {self.max_retries} max retries.\n", "info")
                        self.finished = True
                        continue

                self.action_dispatch(action_type, action_arg)

                self.messages[-1]['content'] += self.current_observation

            if none_action:
                self.logger.log(
                    f"Observation {self.rounds + 1}: No feedback from the environment due to the null action.\n")
            else:
                self.logger.log(f"Observation {self.rounds + 1}: {self.current_observation}\n", "info")

            if action_type and action_type == 'Planner' and self.retry_record['planner'] == 0:
                self.finished = True
                self.answer = self.current_observation
                continue

            self.rounds += 1

        self.set_status("done")
        self.set_end_time(time=time.time())

        return {
            "agent_name": self.agent_name,
            "result": self.answer,
            "rounds": self.rounds,
            "agent_waiting_time": self.start_time - self.created_time,
            "agent_turnaround_time": self.end_time - self.created_time,
            "request_waiting_times": self.request_waiting_times,
            "request_turnaround_times": self.request_turnaround_times,
        }

    def build_system_instruction(self):
        self.messages.append({
            "role": "user", "content": ZEROSHOT_REACT_INSTRUCTION
        })
        self.messages.append({
            "role": "user", "content": "Query: " + self.task_input
        })

    def build_planner_instruction(self, query: str, text: str) -> None:
        self.messages.clear()
        # simply request once
        self.messages.append({
            "role": "user", "content": PLANNER_INSTRUCTION.format(text=text, query=query)
        })

    def is_halted(self) -> bool:
        return self.rounds > self.max_rounds

    def is_finished(self) -> bool:
        return self.finished

    def action_dispatch(self, action_type: str, action_arg: str) -> None:
        """call coresponding tools by action_type

        Args:
            action_type (str): type
            action_arg (str): args
        """

        if action_type == 'Planner':
            query = action_arg
            text = self.tool_list[actionMapping["NotebookWrite"]].list_all()

            # reset the context and build planner agent context
            self.build_planner_instruction(text, query)

            response, start_times, end_times, waiting_times, turnaround_times = self.get_response(
                query=Query(
                    messages=self.messages,
                    tools=None
                )
            )
            self.request_waiting_times.extend(waiting_times)
            self.request_turnaround_times.extend(turnaround_times)

            self.current_observation = to_string(response.response_message)
            self.answer = self.current_observation
            self.current_observation = "\n" + self.current_observation  # align output
            self.__reset_record()

        elif action_type == 'NotebookWrite':
            try:
                action_name = actionMapping[action_type]
                self.current_observation = to_string(self.tool_list[action_name].run(self.current_data, action_arg))
                self.__reset_record()

            except Exception as e:
                self.retry_record[action_name] += 1
                self.current_observation = to_string(e)

        elif action_type in actionMapping.keys():
            try:
                action_name = actionMapping[action_type]
                args = action_arg.split(', ')
                self.current_data = self.tool_list[action_name].run(*args)
                self.current_observation = to_string(self.current_data)
                self.__reset_record()

            except Exception as e:
                self.retry_record[action_name] += 1
                self.current_observation = to_string(e)

        else:
            self.retry_record[INVALID_ACTION] += 1
            self.current_observation = f'''{action_type} is Invalid Action. Valid Actions are
              FlightSearch[Departure City, Destination City, Date] /
              AccommodationSearch[City] /
              RestaurantSearch[City] /
              NotebookWrite[Short Description] /
              AttractionSearch[City] /
              CitySearch[State] /
              GoogleDistanceMatrix[Origin, Destination, Mode] /
              Planner[Query].'''

    def load_city(self, city_set_path: str) -> Set[str]:
        city_set = []
        current_dir = os.path.dirname(os.path.abspath(__file__))
        city_set_path = os.path.join(current_dir, city_set_path)
        lines = open(city_set_path, 'r').read().strip().split('\n')
        for unit in lines:
            city_set.append(unit)
        return set(city_set)

    def __reset_record(self) -> None:
        self.retry_record = {key: 0 for key in self.retry_record}
        self.retry_record[INVALID_ACTION] = 0


def parse_action(string: str):
    """match action type and action arg

    Args:
        string (str): string will be matched

    Returns:
        tuple[str, str]: action type and action arg
    """
    pattern = r'^(\w+)\[(.+)\]$'
    match = re.match(pattern, string)

    try:
        if match:
            action_type = match.group(1)
            action_arg = match.group(2)
            return action_type, action_arg
        else:
            return None, None

    except Exception:
        return None, None


def validate_date_format(date_list: List[str]) -> bool:
    for date in date_list:
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, date):
            return False
    return True


def valid_city_format(city_list: List[str], city_set: Set[str]) -> bool:
    return set(city_list).issubset(city_set)


def to_string(data) -> str:
    if data is not None:
        if type(data) is DataFrame:
            return data.to_string(index=False)
        else:
            return str(data)
    else:
        return str(None)
