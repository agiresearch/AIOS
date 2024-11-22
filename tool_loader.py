from cerebrum.manager.tool import ToolManager

manager = ToolManager('https://my.aios.foundation/')

tool_data = manager.package_tool(r'/Users/rama2r/AIOS/pyopenagi/tools/arxiv')
manager.upload_tool(tool_data)
