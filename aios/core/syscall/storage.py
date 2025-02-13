from aios.core.syscall import Syscall

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
                    "name": {
                        "type": "string",
                        "description": "name of the file",
                    }
                },
                "required": ["name"],
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
                    "name": {
                        "type": "string",
                        "description": "name of the directory",
                    }
                },
                "required": ["name"],
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
                    "name": {
                        "type": "string",
                        "description": "name of the file",
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
                    "name": {
                        "type": "string",
                        "description": "name of the file",
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
                "required": ["name"],
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
                    "name": {
                        "type": "string",
                        "description": "name of the file",
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
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "link",
            "description": "generate a link for a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "name of the file",
                    }
                },
                "required": [],
            },
        },
    }
]
