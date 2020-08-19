import json
import copy
with open('database/experiment-settings.json') as f:
    test_dict = json.load(f)

test_dict_2 = copy.copy(test_dict)
test_dict_2['Game Mode'] = 'test'

print(test_dict)
print(test_dict_2)