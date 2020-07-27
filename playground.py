import json

# with open("database/demons.json", 'r') as f:
#     demon_dict = json.load(f)
#
# with open("database/magatama.json", 'r') as f:
#     magatama_dict = json.load(f)
#
# with open("database/moves.json", 'r') as f:
#     moves_dict = json.load(f)
#
# with open("database/passives.json", 'r') as f:
#     passives_dict = json.load(f)
#
# unimplemented_moves = []
# for demon in demon_dict:
#     base_moves = demon_dict[demon]['Base Moves']
#     for move in base_moves:
#         if move not in moves_dict and move not in passives_dict:
#             unimplemented_moves.append(move)
#     learned_moves = demon_dict[demon]['Learned Moves']
#     for move in learned_moves:
#         if move[0] not in moves_dict and move[0] not in passives_dict:
#             unimplemented_moves.append(move[0])
# for magatama in magatama_dict:
#     moves = magatama_dict[magatama]['Moves']
#     for move in moves:
#         if move[0] not in moves_dict and move[0] not in passives_dict:
#             unimplemented_moves.append(move[0])
# if 'Pierce' not in passives_dict:
#     unimplemented_moves.append('Pierce')
# unimplemented_moves = sorted(list(set(unimplemented_moves)))
# print(unimplemented_moves)

with open("database/moves.json", 'r') as f:
    moves_dict = json.load(f)


def create_special(effect_info={}):
    '''Takes in effect_info dict; updates it to defaults. Used when creating new special effects, usually
    through passives (such as bright/dark might and drain attack)'''
    effect_info.setdefault('Element', 'None')
    effect_info.setdefault('Accuracy', 100)
    effect_info.setdefault('Value', 0)
    effect_info.setdefault('Target', 'Same')
    effect_info.setdefault('Condition', 'None')
    return effect_info


move = moves_dict['Attack']
move['Special Effects']['Dark Might'] = create_special()

print(moves_dict['Attack'])