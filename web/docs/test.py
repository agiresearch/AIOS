import yaml

with open('backend/test.yaml', 'r') as file:
    data = yaml.safe_load(file)

print(data)
