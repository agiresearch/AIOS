from litellm import completion
from aios.core.schema import CoreSchema
from aios.core.types import array, string, integer


def complete(
    name: str,
    message: str,
    system_message: str | None = None,
    temperature: float = 0.3,
    max_tokens: float | None = None,
    json: bool = False,
    schema: CoreSchema | None = None
):
    messages = []

    if system_message:
        messages.append({
            'role': 'system',
            'content': system_message
        })
        
    messages.append({
        'role': 'assistant',
        'content': message
    })

    if not json:
        return completion(
            model=name, 
            temperature=temperature,
            messages=messages,
            max_tokens=max_tokens
        )
    else:
        if schema is None:
            pass

        messages[0] = f"{messages[0]}. \n You always respond in JSON. Use the following schema - \n {schema.to_llm_format()}"

        return completion(
            model=name, 
            temperature=temperature,
            messages=messages,
            max_tokens=max_tokens,
            response_format={ "type": "json_object" },
        )
    
# Example usage
if __name__ == "__main__":
    schema = CoreSchema()

    schema.add_field("hi", array(string), "string of health")
    schema.add_field("cows", integer, "num of cows")

    # Print the LLM-readable format
    print(schema.to_llm_format())