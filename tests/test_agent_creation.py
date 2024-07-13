from pyopenagi.agents.agent_process import AgentProcess
from pyopenagi.utils.chat_template import Query

def test_agent_creation():
    agent_process = AgentProcess(
        agent_name="example/academic_agent",
        query=Query(
            messages = [
                {"role": "user", "content": "Summarize researches of quantum computing in recent five years."}
            ]
        )
    )
    # Use plain assert statements for testing conditions
    assert agent_process.agent_name == "example/academic_agent", "Agent name does not match"
    # Add more assertions here as necessary to validate the properties of the agent_process object
