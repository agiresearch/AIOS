from cerebrum.manager.agent import AgentManager
from cerebrum.manager.tool import ToolManager
from cerebrum.runtime.process import LLMProcessor, RunnableAgent

from .. import config
 
class AutoAgent:
    AGENT_MANAGER = AgentManager('https://my.aios.foundation')
 
    @classmethod
    def from_preloaded(cls, agent_name: str):
        _client = config.global_client

        return RunnableAgent(_client, agent_name)


class AutoLLM:
    @classmethod
    def from_dynamic(cls):
        return LLMProcessor(config.global_client)


class AutoTool:
    TOOL_MANAGER = ToolManager('https://my.aios.foundation')

    @classmethod
    def from_preloaded(cls, tool_name: str):
        if tool_name.split('/')[0] != 'core':
            author, name, version = cls.TOOL_MANAGER.download_tool(
                author=tool_name.split('/')[0],
                name=tool_name.split('/')[1]
            )

            tool, _ = cls.TOOL_MANAGER.load_tool(author, name, version)
        else:
            tool, _ = cls.TOOL_MANAGER.load_tool(local=True, name=tool_name)
        
        #return tool instance, not class
        return tool()
    
    @classmethod
    def from_batch_preload(cls, tool_names: list[str]):
        response = {
             'tools': [],
             'tool_info': []
        }

        for tool_name in tool_names:
             tool = AutoTool.from_preloaded(tool_name)

             response['tools'].append(tool.get_tool_call_format())
             response['tool_info'].append(
                {
                    "name": tool.get_tool_call_format()["function"]["name"],
                    "description": tool.get_tool_call_format()["function"]["description"],
                }
             )


        return response