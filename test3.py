from cerebrum.manager.agent import AgentManager
from cerebrum.manager.tool import ToolManager


# manager = ToolManager('https://my.aios.foundation/')
manager = AgentManager('https://my.aios.foundation/')
agent_data = manager.package_agent(r'/Users/rama2r/AIOS/pyopenagi/agents/example/academic_agent')
# tool_data = manager.package_tool(r'/Users/rama2r/AIOS/pyopenagi/tools/arxiv')
# manager.upload_tool(tool_data)
manager.upload_agent(agent_data)
# print(agent_data)

# manager.upload_agent(agent_data)
# manager.download_tool('example', 'arxiv')

# agent = manager.load_tool('example', 'arxiv', '0.0.12')
# print(agent)
# print(agent)