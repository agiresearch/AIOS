
class Browser:
    def __init__(self):
        self.name = "browser"
        
    def get_tool_call_format(self):
        return {
            "function": {
                "name": "browser",
                "description": "A tool for web browsing operations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to visit"
                        },
                        "action": {
                            "type": "string",
                            "description": "Action to perform",
                            "enum": ["browse", "click", "input"]
                        }
                    },
                    "required": ["url", "action"]
                }
            }
        }
    
    def run(self, params):
        return f"Browsed {params['url']} with action {params['action']}"
