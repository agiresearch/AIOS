from aios.syscall.syscall import Syscall

class StorageSyscall(Syscall):
    pass

storage_syscalls = [
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "create a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "path of the file",
                    }
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_dir",
            "description": "create a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "path of the directory",
                    }
                },
                "required": ["dir_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "delete a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "path of the file",
                    }
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_dir",
            "description": "delete a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "path of the directory",
                    }
                },
                "required": ["dir_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write",
            "description": "write content into a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "path of the file",
                    },
                    "content": {
                        "type": "string",
                        "description": "content to be written into the file",
                    }
                },
                "required": ["file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve",
            "description": "retrieve files and summary the content",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "path of the file",
                    },
                    "k": {
                        "type": "string",
                        "default": "3",
                        "description": "top k files to be retrieved",
                    },
                    "query_text": {
                        "type": "string",
                        "description": "query text used to retrive files",
                    },
                    "keywords": {
                        "type": "string",
                        "description": "keywords must be contained in the doc"
                    }
                },
                "required": ["k", "query_text"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rollback",
            "description": "rollback a file to a specific version",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "path of the file",
                    },
                    "n": {
                        "type": "string",
                        "default": "1",
                        "description": "the number of versions to rollback",
                    },
                    "time": {
                        "type": "string",
                        "description": "the specific time of a file version",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "share",
            "description": "generate a public shareable link for a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "path of the file",
                    },
                    "expires_in": {
                        "type": "string",
                        "default": "7 days",
                        "description": "expiration time of the share link",
                    }
                },
                "required": ["file_path"],
            },
        },
    }
]
