from cerebrum.manager.tool import ToolManager

manager = ToolManager('https://my.aios.foundation')

tool_package = manager.package_tool('/Users/rama2r/Cerebrum/example/tools/arxiv')

manager.upload_tool(tool_package)