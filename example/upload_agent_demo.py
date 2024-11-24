from cerebrum.manager.agent import AgentManager

manager = AgentManager('https://my.aios.foundation')

agent_package = manager.package_agent('/Users/rama2r/Cerebrum/example/agents/academic_agent')

manager.upload_agent(agent_package)