from ...react_agent import ReactAgent
class TravelAgent(ReactAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 agent_process_factory,
                 log_mode: str
        ):
        ReactAgent.__init__(self, agent_name, task_input, agent_process_factory, log_mode)

    def automatic_workflow(self):
        return super().automatic_workflow()

    def manual_workflow(self):
        workflow = [
            {
                "message": "identify the destination and search for hotel locations",
                "tool_use": ["hotel_location_search"]
            },
            {
                "message": "based on the hotel locations, find suitable hotels using the hotel_search tool, and select the best one. ",
                "tool_use": None
            },
            {
                "message": "get detailed information about the selected hotel",
                "tool_use": ["get_hotel_details"]
            },
            {
                "message": ["search for the nearest airport to the origin"],
                "tool_use": ["airport_search"]
            },
            {
                "message": ["search for the nearest airport to the destination"],
                "tool_use": ["airport_search"]
            },
            {
                "message": ["find available flights to the destination airport using the correct date"],
                "tool_use": ["flight_search"]
            },
            {
                "message": ["search for restaurant locations near destination"],
                "tool_use": ["restaurant_location_search"]
            },
            {
                "message": ["based on the restaurant locations, find suitable restaurants"],
                "tool_use": ["restaurant_search"]
            },
            {
                "message": ["get detailed information about the selected restaurants"],
                "tool_use": ["get_restaurant_details"]
            },
            {
                "message": ["Gather additional relevant information about the destination the user is visiting"],
                "tool_use": ["wikipedia"]
            },
            {
                "message": ["integrate the information gathered from the previous steps to provide a comprehensive travel plan"],
                "tool_use": None
            }
        ]
        return workflow

    def run(self):
        return super().run()
