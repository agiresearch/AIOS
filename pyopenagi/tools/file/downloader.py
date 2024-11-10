
class Downloader:
    def __init__(self):
        self.name = "downloader"
        
    def get_tool_call_format(self):
        return {
            "function": {
                "name": "downloader",
                "description": "A tool for downloading files",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL of the file to download"
                        },
                        "path": {
                            "type": "string",
                            "description": "Local path to save the file"
                        }
                    },
                    "required": ["url", "path"]
                }
            }
        }
    
    def run(self, params):
        return f"Downloaded file from {params['url']} to {params['path']}"
