import json
with open("database/demons.json", 'r') as f:
    demon_dict = json.load(f)

print(demon_dict['Gabriel'])
