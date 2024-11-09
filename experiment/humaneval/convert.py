import json

# Load the JSON data
with open('interpreter_prediction.json', 'r') as json_file:
    data = json.load(json_file)

# Write to JSONL file
with open('interpreter_prediction.jsonl', 'w') as jsonl_file:
    for entry in data:
        entry["completion"] = entry["result"]
        entry.pop("result")
        jsonl_file.write(json.dumps(entry) + '\n')
