import requests

from ...utils.utils import get_from_env

from ..base import BaseHuggingfaceTool

import base64

class DocQuestionAnswering(BaseHuggingfaceTool):
    def __init__(self):
        super().__init__()

    def run(self, params):

        API_URL = "https://api-inference.huggingface.co/models/impira/layoutlm-document-qa"
        headers = {"Authorization": "Bearer " + get_from_env("HF_AUTH_TOKENS")}

        question = params["question"]

        path = params["path"]

        with open(path, "rb") as f:
            img = f.read()

        payload = {
             "input": {
                  "image": base64.b64encode(img).decode("utf-8")
             },
             "question": question
        }
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()


    def get_tool_call_format(self):
        tool_call_format = {
            "type": "function",
            "function": {
                "name": "doc_question_answering",
                "description": "answer the question based on the given document",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "question that needs to be answered"
                        },
                        "path": {
                             "type": "string",
                             "description": "path of the document"
                        }
                    },
                    "required": [
                        "question",
                        "path"
                    ]
                }
            }
        }
        return tool_call_format
