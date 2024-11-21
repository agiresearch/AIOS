from cerebrum.manager.agent import AgentManager


manager = AgentManager('https://my.aios.foundation/')
agent_data = manager.package_agent(r'/Users/rama2r/AIOS/pyopenagi/agents/example/academic_agent')

# print(agent_data)

manager.upload_agent(agent_data)
# manager.download_agent('example', 'academic_agent', '0.0.10')

# agent = manager.load_agent('example', 'academic_agent', '0.0.10')
# print(agent)
# print(agent)