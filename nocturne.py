#!/usr/bin/env python
# coding: utf-8

# In[1]:


# to do:

#add hard ai thru reinforcement q-learning

# do bind or stun affect crit rate?

# check if lakshmi has "h"

# crit rate of divine shot is definitely off
# db says 30, putting in 55
# probably off for others?

# anti-expel/death are weird
# https://gamefaqs.gamespot.com/ps2/582958-shin-megami-tensei-nocturne/faqs/35024
# stack with innate resistance
# don't affect direct damage (test)
# how do they affect thunderclap?

# passives give double instances of resistances demon has natively
# should this be removed? or just in display?

# focus doesn't work with multihits?
# check exactly how in-game (deathbound? andalucia?)

# does dekaja effect of hell exhaust trigger on dodge? void?

# does karasu have "base moves"? same as koppa base moves

# setting ice breath to 5 hits instead of 4 to match fire breath/shock/wing buffet
# check?

# sacrifice+endure?

# check how voids/absorbs work if target is stoned

# does guillotine inflict stun?

# check if god's bow misses

# check if last resort misses

# check how queen mab evolution works with base skills

# test if pestilence (pale rider) can miss (listed accuracy is 255)

# missing info on correction/limits of kamikaze/last resort/sacrifice
# check if sacrifice is 4-hit or 5-hit
# rn, guessing missing values

# verify that evil gaze straight misses instead of proccing
# also check print msg

# does recarmdra revive? or just heal?

# dia and diarama formulas are unknown— rn, using agilao/agidyne numbers
# fix print messages to print (health full)

# does drain attack trigger on counter?

# do sleeping demons wake up on any kind of hit?

# check drain attack heal% and crit%

# double-check life stone/chakra drop heal percentage

# can 200 accuracy moves miss? (earthquake, yoshitsune)
# xn site says hit and evasion are calculated differently?

# does freeze chance increase on ice-weak enemies?

# does freezing stop fire repel on surt's attack? (check category or element when redefining effectiveness?)

# fix mp/hp recovery
# mp: should print the actual amount restored, not the hypothetical
# hp: rounding errors?
# combine "heal" and "hp recovery" into effect
# maybe use new attribute in sfx (type? tag? calc?) to differentiate between 3 types
# percentage-based, defined amount, power-based
# calculate in use_move (so we can use the user power), pass into proc_effect
# would have to change how proc_effect works from calculating percentage to adding finite value

# check if tetrakarn reflects all multihits

# normal attack might not trigger counters

# counter doesn't work when user has multihit normals: have to link crits

# check tekisatsu (stinger) crit rate? felt like higher than 4

# check what message displays on 5th debilitate or 3rd taunt

# because extra parameters were added into use_move (hit/crit), some processes can probably be streamlined
# moves that always hit: always-hits? reflects?
# could also be easier to keep as is for a lot of these
# also: go through and fix other apps of use_move

# ui improvements:
# add way to view all demons during selection
# add help function to all user inputs

# make dictionary with effect (in move_dict) as key, long desc as values (for Move.__str__)
# add convo skills?? (later)

# passives (voids, pierce, etc.) that give demons/moves attributes need to reset (if going to implement multi-battles)


# In[2]:


# links:
# english skills: https://aqiu384.github.io/megaten-fusion-tool/smt3/skills
# data notes: https://web.archive.org/web/20160216231006/http://xn--ehqs60c2gs6ptzjh.jp/archives/shin3_skill001.html
# dmg formulas: https://web.archive.org/web/20160216231125/http://xn--ehqs60c2gs6ptzjh.jp/archives/shin3_skill002.html
# mag skills: https://web.archive.org/web/20160415172534/http://xn--ehqs60c2gs6ptzjh.jp/archives/shin3_skill003.html
# phys skills: https://web.archive.org/web/20160515005157/http://xn--ehqs60c2gs6ptzjh.jp/archives/shin3_skill004.html
# more mag formula info: https://web.archive.org/web/20160216231208/http://xn--ehqs60c2gs6ptzjh.jp/archives/shin3_skill006.html
# same: https://web.archive.org/web/20150919135330/http://xn--ehqs60c2gs6ptzjh.jp/archives/shin3_skill007.html
# misc info: https://web.archive.org/web/20160316012050/http://xn--ehqs60c2gs6ptzjh.jp/archives/shin3_skill008.html
# other wiki: https://w.atwiki.jp/noctan/pages/85.html


# In[3]:


#imports
import sys
import timeit
from fuzzywuzzy import process
import random
import operator
import copy
import numpy as np


# In[4]:


#global utility functions

def print_list(items):
    output = ''
    if type(items) is set:
        new_items = list(items)
    else:
        new_items = items
    if len(new_items) == 0:
        return 'None'
    if len(new_items) >= 1:
        for item in new_items[:-1]:
            output += f'{item}, '
    output += str(new_items[-1])
    return output


def except_key(dictionary, subdict_key, key, default):
    subdict = dictionary[subdict_key]
    try:
        output = subdict[key]
    except KeyError:
        output = default
    return copy.deepcopy(output)


def ordinal(n):
    ordinals = ['zeroth', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh',
                'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth', 'thirteenth', 'fourteenth',
                'fifteenth', 'sixteenth']
    if n > len(ordinals) or n < 0:
        raise ValueError('ordinals input number must be between 0 and 16')
    return ordinals[n]


# In[5]:


#global variables

# sorted by level-alpha
# mandatory: level, stats, race
# optional: base/learned moves, attack mods, affinities, evolution
demon_dict = {'Beelzebub Fly': {'Base Moves': [],
                                'Learned Moves': [('Death Flies', 96), ('Victory Cry', 97)],
                                'Attack': {},
                                'Level': 95,
                                'Strength': 35,
                                'Magic': 28,
                                'Vitality': 28,
                                'Agility': 29,
                                'Luck': 21,
                                'Reflect': ['Expel', 'Death'],
                                'Absorb': [],
                                'Void': ['Curse', 'Nerve', 'Mind'],
                                'Resist': ['Phys', 'Ice', 'Elec', 'Force'],
                                'Weaknesses': [],
                                'Race': 'Tyrant',
                                'Evolution': 'None'
                                },
              'Metatron': {'Base Moves': ['Mahamaon', 'Tarukaja', 'Makakaja', 'Debilitate', 'Megidolaon'],
                           'Learned Moves': [('Holy Wrath', 96), ('Fire of Sinai', 97), ('Victory Cry', 98)],
                           'Level': 95, 'Strength': 32, 'Magic': 34, 'Vitality': 29, 'Agility': 24, 'Luck': 16,
                           'Void': ['Expel', 'Death', 'Curse', 'Nerve', 'Mind'], 'Resist': ['Phys', 'Fire',
                                                                                            'Elec', 'Force'],
                           'Race': 'Seraph'},
              'Shiva': {'Base Moves': ['Hassohappa', 'Allure', 'Victory Cry'],
                        'Learned Moves': [('Bolt Storm', 96), ('Avenge', 97), ('Megidolaon', 98),
                                          ('Phys Drain', 99)], 'Level': 95, 'Strength': 32, 'Magic': 26, 'Vitality': 36,
                        'Agility': 26, 'Luck': 15, 'Void': ['Expel', 'Death'],
                        'Resist': ['Phys', 'Fire', 'Ice', 'Elec', 'Force', 'Curse', 'Nerve', 'Mind'],
                        'Race': 'Fury'},
              'Vishnu': {'Base Moves': ['Holy Wrath', 'Hell Gaze', 'Prayer'],
                         'Learned Moves': [('Prominence', 94), ('Hades Blast', 95), ('Radiance', 96),
                                           ('Phys Repel', 97)], 'Level': 93, 'Strength': 27, 'Magic': 35,
                         'Vitality': 25,
                         'Agility': 20, 'Luck': 26, 'Reflect': ['Expel'], 'Void': ['Death'],
                         'Resist': ['Phys', 'Fire', 'Ice', 'Elec', 'Force', 'Curse', 'Nerve', 'Mind'],
                         'Race': 'Deity'},
              'Mot': {'Base Moves': ['Maragidyne', 'Mazandyne', 'Makakaja'], 'Learned Moves':
                  [('Beckon Call', 92), ('Intimidate', 93), ('Force Drain', 94), ('Megidolaon', 95)],
                      'Level': 91, 'Strength': 25, 'Magic': 32, 'Vitality': 31, 'Agility': 16, 'Luck': 19,
                      'Void': ['Expel', 'Death', 'Curse', 'Nerve', 'Mind'], 'Weaknesses': ['Elec'],
                      'Race': 'Tyrant'},
              'Michael': {'Base Moves': ['Deathbound', 'Endure'], 'Learned Moves': [('Victory Cry', 91),
                                                                                    ('Tarukaja', 92),
                                                                                    ('Mana Surge', 93),
                                                                                    ('Megidolaon', 94)], 'Level': 90,
                          'Strength': 29, 'Magic': 30, 'Vitality': 23, 'Agility': 25, 'Luck': 18,
                          'Reflect': ['Expel'], 'Void': ['Fire', 'Ice', 'Elec', 'Force'], 'Race': 'Seraph'},
              'Gabriel': {'Base Moves': ['Maziodyne', 'Ziodyne', 'Samarecarm'], 'Learned Moves':
                  [('Blight', 88), ('Persuade', 89), ('Elec Boost', 90), ('Radiance', 91)], 'Level': 87,
                          'Strength': 24, 'Magic': 30, 'Vitality': 22, 'Agility': 24, 'Luck': 12,
                          'Reflect': ['Expel'], 'Void': ['Fire', 'Ice', 'Force'], 'Race': 'Seraph'},
              'Beelzebub': {'Base Moves': ['Maziodyne', 'Megidolaon'], 'Learned Moves': [('Watchful', 85),
                                                                                         ('Elec Boost', 86)],
                            'Level': 84, 'Strength': 32, 'Magic': 27, 'Vitality': 27,
                            'Agility': 19, 'Luck': 19, 'Reflect': ['Expel', 'Death'], 'Void': ['Curse',
                                                                                               'Nerve', 'Mind'],
                            'Resist': ['Phys', 'Ice', 'Elec', 'Force'], 'Race': 'Tyrant',
                            'Evolution': ('Beelzebub Fly', 86)},
              'Raphael': {'Base Moves': ['Makarakarn', 'Tetrakarn', 'Mana Refill'], 'Learned Moves':
                  [('Prayer', 85), ('Mahamaon', 86), ('Stasis Blade', 87), ('Holy Wrath', 88)],
                          'Level': 84, 'Strength': 26, 'Magic': 26, 'Vitality': 22, 'Agility': 28, 'Luck': 17,
                          'Reflect': ['Expel'], 'Void': ['Fire', 'Force'], 'Race': 'Seraph'},
              'Mada': {'Base Moves': ['Hades Blast', 'Debilitate', 'Blackmail'], 'Learned Moves':
                  [('Intoxicate', 84), ('Diarahan', 85), ('Tarukaja', 86), ('Life Surge', 87)],
                       'Level': 83, 'Strength': 30, 'Magic': 21, 'Vitality': 30, 'Agility': 14, 'Luck': 16,
                       'Absorb': ['Phys'], 'Void': ['Death'], 'Weaknesses': ['Curse'], 'Race': 'Vile'},
              'Ongyo-Ki': {'Base Moves': ['Dark Sword', 'Beckon Call', 'Tentarafoo'], 'Learned Moves':
                  [('Megido', 82), ('Blackmail', 83), ('Mudoon', 84), ('Blight', 85),
                   ('Victory Cry', 86)], 'Level': 81, 'Strength': 23, 'Magic': 27, 'Vitality': 23,
                           'Agility': 20, 'Luck': 11, 'Void': ['Phys', 'Death', 'Curse', 'Mind'],
                           'Weaknesses': ['Expel'], 'Race': 'Brute'},
              'Lilith': {'Base Moves': ['Maziodyne', 'Hell Gaze', 'Allure'], 'Learned Moves':
                  [('Mana Drain', 81), ('Hell Fang', 82), ('Mana Surge', 83), ('Megidola', 84)],
                         'Level': 80, 'Strength': 17, 'Magic': 30, 'Vitality': 21, 'Agility': 17, 'Luck': 15,
                         'Void': ['Expel', 'Death'], 'Resist': ['Fire', 'Ice', 'Elec', 'Force'], 'Race': 'Night'},
              'Raidou Kuzunoha XIV': {'Base Moves': ['Boogie-Woogie', 'Yoshitsune Show-Up',
                                                     'Mishaguji Thunder', 'Hitokoto Gust', 'Guardian Raptor', 'Provoke',
                                                     'Arbitration', 'Endure'],
                                      'Learned Moves': [('Mokoi Boomerang', 81),
                                                        ('Tekisatsu', 82), ('Raidou the Aeon', 83),
                                                        ('Jiraiya Tarantella', 84)],
                                      'Level': 80, 'Strength': 25, 'Magic': 22, 'Vitality': 22, 'Agility': 25,
                                      'Luck': 16, 'Void': ['Expel', 'Death', 'Curse', 'Nerve', 'Mind'],
                                      'Resist': ['Phys', 'Fire', 'Ice', 'Elec', 'Force'], 'Race': 'Summoner'},
              'Mithra': {'Base Moves': ['Mamudoon', 'Megidola', 'Debilitate'], 'Learned Moves':
                  [('Death Pact', 79), ('Holy Wrath', 80), ('Fog Breath', 81), ('Mahamaon', 82),
                   ('Mana Surge', 83)], 'Level': 78, 'Strength': 27, 'Magic': 25, 'Vitality': 27,
                         'Agility': 16, 'Luck': 18, 'Reflect': ['Phys'], 'Void': ['Expel', 'Death'],
                         'Weaknesses': ['Ice'], 'Race': 'Deity'},
              'Aciel': {'Learned Moves': [('Life Surge', 78), ('Tetrakarn', 79), ('Hell Fang', 80),
                                          ('Victory Cry', 81)], 'Level': 77, 'Strength': 29, 'Magic': 25,
                        'Vitality': 27,
                        'Agility': 14, 'Luck': 16, 'Reflect': ['Death'], 'Void': ['Expel'],
                        'Resist': ['Fire', 'Ice', 'Elec', 'Force'], 'Race': 'Tyrant'},
              'Trumpeter': {'Base Moves': ['Maragidyne', 'Mabufudyne', 'Maziodyne', 'Mazandyne', 'Holy Melody'],
                            'Learned Moves': [('Makakaja', 78), ('Dekaja', 79), ('Megidolaon', 80),
                                              ('Evil Melody', 81)], 'Level': 77, 'Strength': 21, 'Magic': 31,
                            'Vitality': 21,
                            'Agility': 24, 'Luck': 15, 'Void': ['Expel', 'Death', 'Curse', 'Nerve', 'Mind'],
                            'Race': 'Fiend'},
              'Thor': {'Base Moves': ['Hades Blast', 'Ziodyne', 'Avenge'], 'Learned Moves':
                  [('Mediarahan', 77), ('Maziodyne', 78), ('Stasis Blade', 79), ('Fire Repel', 80)],
                       'Level': 76, 'Strength': 28, 'Magic': 20, 'Vitality': 26, 'Agility': 12, 'Luck': 17,
                       'Void': ['Elec', 'Expel'], 'Weaknesses': ['Curse', 'Nerve'], 'Race': 'Kishin'},
              'Hresvelgr': {'Base Moves': ['Mabufudyne', 'Wing Buffet', 'Ice Boost'], 'Learned Moves':
                  [('Anti-Phys', 76), ('Iron Claw', 77), ('Life Refill', 78), ('Elec Repel', 79)],
                            'Level': 75, 'Strength': 20, 'Magic': 20, 'Vitality': 19, 'Agility': 25, 'Luck': 11,
                            'Reflect': ['Ice'], 'Void': ['Death'], 'Weaknesses': ['Fire'], 'Race': 'Wilder'},
              'Skadi': {'Learned Moves': [('Makajamon', 75), ('Makakaja', 76), ('Elec Repel', 77),
                                          ('Earthquake', 78)], 'Level': 74, 'Strength': 23, 'Magic': 29, 'Vitality': 21,
                        'Agility': 18, 'Luck': 15, 'Void': ['Force', 'Expel', 'Curse'], 'Weaknesses': ['Elec'],
                        'Race': 'Lady'},
              'Surt': {'Base Moves': ['Heat Wave', 'Hellfire', 'War Cry'], 'Learned Moves':
                  [('Elec Drain', 75), ('Attack All', 76), ('Wooing', 77), ('Ragnarok', 78)],
                       'Attack': {'Element': 'Fire'}, 'Level': 74, 'Strength': 28, 'Magic': 20, 'Vitality': 24,
                       'Agility': 15, 'Luck': 19, 'Absorb': ['Fire'], 'Void': ['Death', 'Curse', 'Nerve', 'Mind'],
                       'Resist': ['Expel'], 'Weaknesses': ['Ice'], 'Race': 'Tyrant'},
              'Samael': {'Base Moves': ['Prominence', 'Mahamaon', 'Mamudoon'], 'Learned Moves':
                  [('Samarecarm', 74), ('Tetrakarn', 75), ('Avenge', 76), ('Phys Repel', 77)],
                         'Level': 73, 'Strength': 19, 'Magic': 26, 'Vitality': 23, 'Agility': 19, 'Luck': 16,
                         'Reflect': ['Expel', 'Death'], 'Weaknesses': ['Elec'], 'Race': 'Vile'},
              'Uriel': {'Learned Moves': [('Heat Wave', 74), ('Drain Attack', 75), ('Megidola', 76),
                                          ('Radiance', 77)], 'Level': 73, 'Strength': 25, 'Magic': 24, 'Vitality': 20,
                        'Agility': 21, 'Luck': 18, 'Reflect': ['Expel'], 'Void': ['Fire'], 'Race': 'Seraph'},
              'Bishamon': {'Base Moves': ['Thunderclap', 'Attack All'], 'Learned Moves': [('Prominence', 73),
                                                                                          ('Fire Boost', 74),
                                                                                          ('Detain', 75),
                                                                                          ('Endure', 76),
                                                                                          ('Hassohappa', 77)],
                           'Level': 72,
                           'Strength': 25, 'Magic': 18, 'Vitality': 25, 'Agility': 17, 'Luck': 15,
                           'Reflect': ['Fire'], 'Void': ['Expel'], 'Weaknesses': ['Ice'], 'Race': 'Kishin'},
              'Rangda': {'Base Moves': ['Stun Claw', 'Debilitate', 'Dekaja'], 'Learned Moves':
                  [('Mana Refill', 73), ('Makajamon', 74), ('Hellfire', 75), ('Avenge', 76)],
                         'Level': 72, 'Strength': 19, 'Magic': 24, 'Vitality': 20, 'Agility': 14, 'Luck': 15,
                         'Reflect': ['Phys'], 'Weaknesses': ['Elec'], 'Race': 'Femme'},
              'Nyx': {'Base Moves': ['Dormina', 'Eternal Rest', 'Makarakarn'], 'Learned Moves':
                  [('Debilitate', 71), ('Mana Drain', 72), ('Glacial Blast', 73), ('Fire Drain', 74)],
                      'Level': 70, 'Strength': 15, 'Magic': 27, 'Vitality': 17, 'Agility': 16, 'Luck': 15,
                      'Resist': ['Fire', 'Ice', 'Elec', 'Force'], 'Race': 'Night'},
              'Abaddon': {'Base Moves': ['Panic Voice', 'Attack All'], 'Learned Moves': [('Mabufudyne', 70),
                                                                                         ('Intimidate', 71),
                                                                                         ('Retaliate', 72),
                                                                                         ('Ice Repel', 73),
                                                                                         ('Hades Blast', 74)],
                          'Level': 69, 'Strength': 26, 'Magic': 24, 'Vitality': 25, 'Agility': 13, 'Luck': 15,
                          'Reflect': ['Death'], 'Void': ['Expel'], 'Resist': ['Fire', 'Ice', 'Elec', 'Force'],
                          'Race': 'Tyrant', 'Evolution': ('Aciel', 74)},
              'The Harlot': {'Base Moves': ['Maziodyne', 'Death Lust', 'Makajamon'], 'Learned Moves':
                  [('Dekunda', 70), ('Focus', 71), ('Beast Roar', 72)], 'Attack': {'Hits': 7},
                             'Level': 69, 'Strength': 23, 'Magic': 24, 'Vitality': 19, 'Agility': 19, 'Luck': 19,
                             'Reflect': ['Phys'], 'Absorb': ['Elec'],
                             'Void': ['Expel', 'Death', 'Curse', 'Nerve', 'Mind'], 'Race': 'Fiend'},
              'Flauros': {'Base Moves': ['Iron Claw', 'War Cry', 'Blackmail'], 'Learned Moves':
                  [('Deathbound', 69), ('Endure', 70), ('Hades Blast', 71), ('Life Surge', 72),
                   ('Hassohappa', 73)], 'Level': 68, 'Strength': 27, 'Magic': 14, 'Vitality': 22,
                          'Agility': 13, 'Luck': 12, 'Void': ['Death'], 'Weaknesses': ['Nerve'], 'Race': 'Fallen'},
              'Kali': {'Base Moves': ['Deathbound', 'Tentarafoo'], 'Learned Moves': [('Avenge', 68),
                                                                                     ('Fog Breath', 69),
                                                                                     ('Life Surge', 70),
                                                                                     ('Dark Sword', 71)], 'Level': 67,
                       'Strength': 25,
                       'Magic': 19, 'Vitality': 23, 'Agility': 19, 'Luck': 13, 'Reflect': ['Death'],
                       'Void': ['Fire', 'Expel'], 'Weaknesses': ['Ice'], 'Race': 'Lady'},
              'Atropos': {'Base Moves': ['Bufudyne', 'Ziodyne', 'Zandyne'], 'Learned Moves':
                  [('Elec Boost', 68), ('Force Boost', 69), ('Ice Boost', 70), ('Mana Surge', 71),
                   ('Megidola', 72)], 'Level': 67, 'Strength': 16, 'Magic': 28, 'Vitality': 17,
                          'Agility': 15, 'Luck': 14, 'Void': ['Expel', 'Death', 'Mind'], 'Race': 'Femme'},
              'Yurlungur': {'Base Moves': ['Bolt Storm', 'Ziodyne', 'Rakukaja'], 'Learned Moves':
                  [('Elec Boost', 67), ('Mediarahan', 68), ('Samarecarm', 69), ('Wind Cutter', 70)],
                            'Level': 66, 'Strength': 18, 'Magic': 16, 'Vitality': 30, 'Agility': 9, 'Luck': 13,
                            'Void': ['Fire', 'Ice', 'Elec', 'Force'], 'Weaknesses': ['Curse', 'Nerve', 'Mind'],
                            'Race': 'Snake'},
              'Fuu-Ki': {'Base Moves': ['Mazandyne', 'Zandyne'], 'Learned Moves': [('Binding Cry', 67),
                                                                                   ('Chaos Blade', 68),
                                                                                   ('Dark Might', 69),
                                                                                   ('Fog Breath', 70)], 'Level': 66,
                         'Strength': 18, 'Magic': 21, 'Vitality': 20, 'Agility': 19, 'Luck': 11,
                         'Void': ['Force', 'Death'], 'Race': 'Brute'},
              'Black Frost': {'Base Moves': ['Berserk', 'Mabufudyne', 'Mamudoon'], 'Learned Moves':
                  [('Diarama', 67), ('Void Curse', 68), ('Void Nerve', 69), ('Void Mind', 70)],
                              'Level': 66, 'Strength': 24, 'Magic': 24, 'Vitality': 13, 'Agility': 16, 'Luck': 24,
                              'Reflect': ['Fire', 'Death'], 'Absorb': ['Ice'], 'Void': ['Expel'], 'Resist':
                                  ['Phys'], 'Race': 'Night'},
              'Odin': {'Base Moves': ['Agidyne', 'Bufudyne'], 'Learned Moves': [('Deathbound', 66),
                                                                                ('Makajamon', 67), ('Persuade', 68),
                                                                                ('Mabufudyne', 69), ('Maragidyne', 70)],
                       'Level': 65,
                       'Strength': 24, 'Magic': 25, 'Vitality': 18, 'Agility': 17, 'Luck': 16, 'Void':
                           ['Ice', 'Expel'], 'Weaknesses': ['Force'], 'Race': 'Deity'},
              'Tao Tie': {'Base Moves': ['Megido', 'Tetraja', 'Loan'], 'Learned Moves': [('Life Drain', 66),
                                                                                         ('Hell Gaze', 67),
                                                                                         ('Mana Aid', 68),
                                                                                         ('Makajamon', 69)],
                          'Level': 65, 'Strength': 18,
                          'Magic': 21, 'Vitality': 21, 'Agility': 15, 'Luck': 18, 'Void': ['Death'],
                          'Weaknesses': ['Curse'], 'Race': 'Vile'},
              'Scathach': {'Base Moves': ['Mazandyne', 'Might'], 'Learned Moves': [('Force Repel', 65),
                                                                                   ('Dark Pledge', 66),
                                                                                   ('Thunderclap', 67),
                                                                                   ('Mana Aid', 68),
                                                                                   ('Wind Cutter', 69)],
                           'Level': 64, 'Strength': 21, 'Magic': 26, 'Vitality': 17, 'Agility': 18, 'Luck': 15,
                           'Void': ['Force', 'Expel', 'Curse'], 'Weaknesses': ['Elec'], 'Race': 'Megami',
                           'Evolution': ('Skadi', 69)},
              'Throne': {'Base Moves': ['Prominence', 'Mahamaon', 'Brainwash'], 'Learned Moves':
                  [('Mediarahan', 65), ('Mute Gaze', 66), ('Holy Wrath', 67), ('Debilitate', 68)],
                         'Level': 64, 'Strength': 18, 'Magic': 22, 'Vitality': 18, 'Agility': 15, 'Luck': 15,
                         'Reflect': ['Expel'], 'Absorb': ['Fire'], 'Weaknesses': ['Ice', 'Death'],
                         'Race': 'Divine', 'Evolution': ('Uriel', 68)},
              'Albion': {'Learned Moves': [('Drain Attack', 65), ('Phys Drain', 66), ('Recarmdra', 67),
                                           ('Hades Blast', 68)], 'Level': 64, 'Strength': 25, 'Magic': 20,
                         'Vitality': 25,
                         'Agility': 10, 'Luck': 16, 'Void': ['Phys', 'Ice', 'Expel'], 'Race': 'Entity'},
              'Futomimi': {'Base Moves': ['Lunge', 'Mute Gaze', 'Focus', 'War Cry'], 'Learned Moves':
                  [('Might', 64), ('Life Surge', 65), ('Mana Surge', 66)], 'Level': 63, 'Strength': 20,
                           'Magic': 16, 'Vitality': 20, 'Agility': 15, 'Luck': 12, 'Void':
                               ['Expel', 'Death', 'Curse', 'Nerve', 'Mind'], 'Race': 'Kishin'},
              'Lachesis': {'Base Moves': ['Makakaja', 'Makarakarn', 'Rakukaja'], 'Learned Moves':
                  [('Sukukaja', 64), ('Dormina', 65), ('Tetrakarn', 66), ('Rakunda', 67),
                   ('Trafuri', 68)], 'Level': 63, 'Strength': 16, 'Magic': 26, 'Vitality': 19,
                           'Agility': 10, 'Luck': 15, 'Void': ['Curse', 'Nerve', 'Mind'], 'Race': 'Femme'},
              'Rakshasa': {'Base Moves': ['Stun Claw', 'Sacrifice'], 'Learned Moves': [('Life Drain', 64),
                                                                                       ('Rakunda', 65),
                                                                                       ('Retaliate', 66),
                                                                                       ('Megido', 67), ('Berserk', 68)],
                           'Level': 63,
                           'Strength': 22, 'Magic': 20, 'Vitality': 16, 'Agility': 11, 'Luck': 14,
                           'Reflect': ['Death'], 'Weaknesses': ['Elec', 'Expel'], 'Race': 'Haunt'},
              'Garuda': {'Learned Moves': [('Mahamaon', 64), ('Persuade', 65), ('Wind Cutter', 66),
                                           ('Endure', 67)], 'Level': 63, 'Strength': 22, 'Magic': 18, 'Vitality': 19,
                         'Agility': 24,
                         'Luck': 12, 'Reflect': ['Expel'], 'Void': ['Curse', 'Nerve'], 'Weaknesses': ['Death'],
                         'Race': 'Avian'},
              'Gurr': {'Base Moves': ['Mazandyne', 'Zandyne', 'Fog Breath'], 'Learned Moves':
                  [('Mamudoon', 64), ('Flatter', 65), ('Wind Cutter', 66), ('Bolt Storm', 67),
                   ('Avenge', 68)], 'Level': 63, 'Strength': 18, 'Magic': 22, 'Vitality': 19, 'Agility': 24,
                       'Luck': 12, 'Reflect': ['Death'], 'Void': ['Curse', 'Nerve', 'Mind'],
                       'Weaknesses': ['Expel'], 'Race': 'Raptor'},
              'Pale Rider': {'Base Moves': ['Mabufudyne', 'Pestilence'], 'Learned Moves': [('Eternal Rest', 64),
                                                                                           ('Blight', 65),
                                                                                           ('Dark Might', 66),
                                                                                           ('Bright Might', 67)],
                             'Level': 63,
                             'Strength': 24, 'Magic': 26, 'Vitality': 18, 'Agility': 17, 'Luck': 13,
                             'Void': ['Ice', 'Expel', 'Death', 'Curse', 'Nerve', 'Mind'], 'Race': 'Fiend'},
              'Sui-Ki': {'Base Moves': ['Glacial Blast', 'Dekaja', 'Ice Boost'], 'Learned Moves':
                  [('Evil Gaze', 63), ('Bufudyne', 64), ('Scout', 65), ('Life Aid', 66)], 'Level': 62,
                         'Strength': 18, 'Magic': 24, 'Vitality': 20, 'Agility': 14, 'Luck': 9,
                         'Void': ['Ice', 'Curse'], 'Weaknesses': ['Fire'], 'Race': 'Brute'},
              'Beiji-Weng': {'Base Moves': ['Stasis Blade', 'Thunderclap', 'Mana Aid'], 'Learned Moves':
                  [('Hell Gaze', 62), ('Wooing', 63), ('Mamudoon', 64), ('Holy Wrath', 65)],
                             'Level': 61, 'Strength': 23, 'Magic': 24, 'Vitality': 23, 'Agility': 14, 'Luck': 12,
                             'Void': ['Expel', 'Death'], 'Resist': ['Phys'], 'Weaknesses': ['Fire'],
                             'Race': 'Fury'},
              'Cerberus': {'Base Moves': ['Iron Claw', 'Binding Cry', 'Fog Breath'], 'Learned Moves':
                  [('Retaliate', 62), ('Detain', 63), ('Hellfire', 64), ('Attack All', 65)],
                           'Level': 61, 'Strength': 23, 'Magic': 14, 'Vitality': 15, 'Agility': 17, 'Luck': 12,
                           'Reflect': ['Fire'], 'Resist': ['Phys'], 'Weaknesses': ['Ice'], 'Race': 'Beast'},
              'Black Rider': {'Base Moves': ['Glacial Blast', 'Soul Divide'], 'Learned Moves':
                  [('Mana Drain', 62), ('Mamudoon', 63), ('Megidola', 64), ('Mana Surge', 65),
                   ('Megidolaon', 66)], 'Level': 61, 'Strength': 22, 'Magic': 25, 'Vitality': 16,
                              'Agility': 20, 'Luck': 13, 'Absorb': ['Ice'], 'Void':
                                  ['Expel', 'Death', 'Curse', 'Nerve', 'Mind'], 'Race': 'Fiend'},
              'Barong': {'Base Moves': ['Bolt Storm', 'Binding Cry'], 'Learned Moves': [('Iron Claw', 61),
                                                                                        ('Mediarahan', 62),
                                                                                        ('Glacial Blast', 63),
                                                                                        ('Void Death', 64)],
                         'Level': 60,
                         'Strength': 22, 'Magic': 22, 'Vitality': 16, 'Agility': 16, 'Luck': 14,
                         'Reflect': ['Expel'], 'Absorb': ['Elec'], 'Weaknesses': ['Death'], 'Race': 'Avatar'},
              'Kin-Ki': {'Base Moves': ['Berserk', 'Focus', 'Rakukaja'], 'Learned Moves': [('Taunt', 60),
                                                                                           ('Sacrifice', 61),
                                                                                           ('Loan', 62),
                                                                                           ('Tempest', 63)],
                         'Level': 59, 'Strength': 23,
                         'Magic': 13, 'Vitality': 24, 'Agility': 7, 'Luck': 15, 'Resist': ['Phys'],
                         'Weaknesses': ['Curse'], 'Race': 'Brute'},
              'Decarabia': {'Base Moves': ['Tetrakarn', 'Analyze', 'Haggle'], 'Learned Moves':
                  [('Sukukaja', 59), ('Hell Gaze', 60), ('Eternal Rest', 61), ('Trafuri', 62),
                   ('Megido', 63)], 'Level': 58, 'Strength': 15, 'Magic': 22, 'Vitality': 17,
                            'Agility': 12, 'Luck': 12, 'Void': ['Death'], 'Resist':
                                ['Fire', 'Ice', 'Elec', 'Force'], 'Race': 'Fallen'},
              'Clotho': {'Base Moves': ['Mahama', 'Hell Gaze', 'Nag'], 'Learned Moves':
                  [('Mediarahan', 59), ('Eternal Rest', 60), ('Allure', 61), ('Samarecarm', 62)],
                         'Level': 58, 'Strength': 16, 'Magic': 22, 'Vitality': 15, 'Agility': 16, 'Luck': 12,
                         'Void': ['Expel', 'Death'], 'Race': 'Femme'},
              'Girimehkala': {'Base Moves': ['Chaos Blade', 'Binding Cry'], 'Learned Moves':
                  [('Dismal Tune', 59), ('Shock', 60), ('Debilitate', 61), ('Tempest', 62)],
                              'Level': 58, 'Strength': 22, 'Magic': 17, 'Vitality': 21, 'Agility': 13,
                              'Luck': 13, 'Reflect': ['Phys'], 'Void': ['Death'], 'Race': 'Vile'},
              'Ganesha': {'Learned Moves': [('Endure', 59), ('Force Drain', 60), ('Debilitate', 61),
                                            ('Tempest', 62)], 'Level': 58, 'Strength': 21, 'Magic': 21, 'Vitality': 21,
                          'Agility': 12, 'Luck': 13, 'Void': ['Ice', 'Force', 'Expel'], 'Weaknesses': ['Elec'],
                          'Race': 'Wargod'},
              'Parvati': {'Learned Moves': [('Mediarama', 58), ('Tetrakarn', 59), ('Thunderclap', 60),
                                            ('Radiance', 61)], 'Level': 57, 'Strength': 15, 'Magic': 23, 'Vitality': 15,
                          'Agility': 16, 'Luck': 20, 'Reflect': ['Expel'], 'Absorb': ['Fire'],
                          'Weaknesses': ['Ice'], 'Race': 'Lady'},
              'Titania': {'Base Moves': ['Glacial Blast', 'Pester'], 'Learned Moves': [('Mediarahan', 58),
                                                                                       ('Pulinpa', 59),
                                                                                       ('Charisma', 60),
                                                                                       ('Mana Surge', 61),
                                                                                       ('Prayer', 62)], 'Level': 57,
                          'Strength': 14, 'Magic': 23, 'Vitality': 15, 'Agility': 12, 'Luck': 13,
                          'Reflect': ['Expel', 'Death'], 'Resist': ['Fire', 'Ice', 'Elec', 'Force'],
                          'Race': 'Fairy'},
              'Amaterasu': {'Base Moves': ['Prominence', 'Tetrakarn'], 'Learned Moves': [('Godly Light', 57),
                                                                                         ('Debilitate', 58),
                                                                                         ('Fire Repel', 59),
                                                                                         ('Prayer', 60)], 'Level': 56,
                            'Strength': 19, 'Magic': 23, 'Vitality': 17, 'Agility': 16, 'Luck': 16,
                            'Void': ['Fire', 'Expel', 'Death'], 'Race': 'Deity'},
              'Queen Mab': {'Base Moves': ['Ziodyne', 'Mediarama', 'Tarukaja'], 'Learned Moves':
                  [('Diarahan', 57), ('Makarakarn', 58), ('Dormina', 59), ('Tetraja', 60),
                   ('Maziodyne', 61)], 'Level': 56, 'Strength': 12, 'Magic': 27, 'Vitality': 12,
                            'Agility': 12, 'Luck': 19, 'Resist': ['Fire', 'Ice', 'Elec', 'Force'],
                            'Race': 'Night'},
              'Chimera': {'Base Moves': ['Fire Breath', 'War Cry', 'Fire Boost'], 'Learned Moves':
                  [('Iron Claw', 56), ('Kidnap', 57), ('Kamikaze', 58), ('Sonic Wave', 59)],
                          'Level': 55, 'Strength': 23, 'Magic': 13, 'Vitality': 16, 'Agility': 17, 'Luck': 10,
                          'Absorb': ['Fire'], 'Void': ['Expel'], 'Weaknesses': ['Nerve', 'Mind'],
                          'Race': 'Holy'},
              'Quetzacoatl': {'Base Moves': ['Stone Bite', 'Glacial Blast', 'Gonnection'], 'Learned Moves':
                  [('Berserk', 56), ('Ice Boost', 57), ('Ice Drain', 58), ('Toxic Cloud', 59),
                   ('Recarmdra', 60)], 'Level': 55, 'Strength': 16, 'Magic': 12, 'Vitality': 27,
                              'Agility': 9, 'Luck': 11, 'Void': ['Ice'], 'Resist': ['Phys'],
                              'Weaknesses': ['Elec'], 'Race': 'Snake'},
              'Gogmagog': {'Base Moves': ['Berserk', 'Tornado', 'Mediarama'], 'Learned Moves':
                  [('Life Surge', 56), ('Tarunda', 57), ('Evil Gaze', 58), ('Rakunda', 59),
                   ('Sukunda', 60)], 'Level': 55, 'Strength': 22, 'Magic': 14, 'Vitality': 21,
                           'Agility': 7, 'Luck': 14, 'Void': ['Phys', 'Ice', 'Death'], 'Weaknesses': ['Fire'],
                           'Race': 'Jirae', 'Evolution': ('Albion', 60)},
              'Red Rider': {'Base Moves': ['Terrorblade', 'Wind Cutter'], 'Learned Moves': [('Bolt Storm', 56),
                                                                                            ('Dekunda', 57),
                                                                                            ('Avenge', 68)],
                            'Level': 55, 'Strength': 23, 'Magic': 21,
                            'Vitality': 18, 'Agility': 15, 'Luck': 13, 'Void':
                                ['Elec', 'Force', 'Expel', 'Death', 'Curse', 'Nerve', 'Mind'], 'Race': 'Fiend'},
              'Lakshmi': {'Base Moves': ['Mediarahan', 'Seduce'], 'Learned Moves': [('Mana Aid', 55),
                                                                                    ('Stone Gaze', 56),
                                                                                    ('Mana Surge', 57),
                                                                                    ('Samarecarm', 58),
                                                                                    ('Recarmdra', 59)],
                          'Level': 54, 'Strength': 14, 'Magic': 24, 'Vitality': 15, 'Agility': 13, 'Luck': 16,
                          'Reflect': ['Expel'], 'Void': ['Curse', 'Nerve', 'Mind'], 'Weaknesses': ['Force'],
                          'Race': 'Megami'},
              'Wu Kong': {'Learned Moves': [('Hassohappa', 55), ('Dark Pledge', 56), ('Attack All', 57),
                                            ('Avenge', 58)], 'Level': 54, 'Strength': 22, 'Magic': 13, 'Vitality': 18,
                          'Agility': 20, 'Luck': 16, 'Void': ['Phys', 'Expel', 'Death'], 'Race': 'Fury'},
              'Sparna': {'Base Moves': ['Zandyne', 'Fog Breath', 'Sukukaja'], 'Learned Moves': [('Mazandyne', 55),
                                                                                                ('Venom Claw', 56),
                                                                                                ('Stone Hunt', 57),
                                                                                                ('Diarahan', 58)],
                         'Level': 54, 'Strength': 13,
                         'Magic': 19, 'Vitality': 14, 'Agility': 22, 'Luck': 11, 'Reflect': ['Force'],
                         'Void': ['Curse', 'Nerve', 'Mind'], 'Race': 'Avian', 'Evolution': ('Garuda', 58)},
              'Shiki-Ouji': {'Base Moves': ['Stun Needle', 'Mamudoon', 'Dekaja'], 'Learned Moves':
                  [('Brainwash', 55), ('Mute Gaze', 56), ('Mahamaon', 57), ('Megido', 58)],
                             'Level': 54, 'Strength': 14, 'Magic': 24, 'Vitality': 16, 'Agility': 10,
                             'Luck': 10, 'Reflect': ['Expel', 'Death'], 'Void': ['Phys'],
                             'Weaknesses': ['Fire'], 'Race': 'Brute'},
              'Loa': {'Base Moves': ['Mamudo', 'Dekunda', 'Tetraja'], 'Learned Moves': [('Venom Bite', 54),
                                                                                        ('Stone Gaze', 55),
                                                                                        ('Last Resort', 56),
                                                                                        ('Mamudoon', 57),
                                                                                        ('Debilitate', 58)],
                      'Level': 53, 'Strength': 16, 'Magic': 22, 'Vitality': 16, 'Agility': 12, 'Luck': 7,
                      'Void': ['Death', 'Curse', 'Nerve'], 'Weaknesses': ['Expel'], 'Race': 'Night'},
              'Jikoku': {'Base Moves': ['Stasis Blade', 'Diarahan'], 'Learned Moves': [('Dekunda', 53),
                                                                                       ('Bufudyne', 54),
                                                                                       ('Dark Pledge', 55),
                                                                                       ('Mazandyne', 56),
                                                                                       ('Bolt Storm', 57)],
                         'Level': 52, 'Strength': 21, 'Magic': 16, 'Vitality': 19, 'Agility': 11, 'Luck': 12,
                         'Reflect': ['Ice'], 'Void': ['Expel'], 'Weaknesses': ['Fire'], 'Race': 'Kishin'},
              'Efreet': {'Base Moves': ['Agidyne', 'Taunt'], 'Learned Moves': [('Makakaja', 53),
                                                                               ('Mana Refill', 54), ('Maragidyne', 55),
                                                                               ('Beckon Call', 56), ('Prominence', 57)],
                         'Level': 52, 'Strength': 15, 'Magic': 23, 'Vitality': 15, 'Agility': 14, 'Luck': 9,
                         'Absorb': ['Fire'], 'Weaknesses': ['Ice'], 'Race': 'Yoma'},
              'Dakini': {'Base Moves': ['Dismal Tune', 'Life Aid'], 'Learned Moves': [('Mamudo', 53),
                                                                                      ('Kidnap', 54), ('Agidyne', 55),
                                                                                      ('Blight', 56), ('Endure', 57)],
                         'Level': 52,
                         'Strength': 21, 'Magic': 11, 'Vitality': 17, 'Agility': 13, 'Luck': 10,
                         'Resist': ['Fire'], 'Weaknesses': ['Ice'], 'Race': 'Femme'},
              'Loki': {'Base Moves': ['Mabufudyne', 'Makajamon'], 'Learned Moves': [('Mischief', 53),
                                                                                    ('Charisma', 54), ('Trafuri', 55),
                                                                                    ('Mudoon', 56), ('Mana Gain', 57)],
                       'Level': 52,
                       'Strength': 16, 'Magic': 20, 'Vitality': 20, 'Agility': 12, 'Luck': 16,
                       'Resist': ['Phys', 'Fire', 'Ice', 'Elec', 'Force', 'Curse', 'Nerve', 'Mind'],
                       'Race': 'Tyrant'},
              'Shadow': {'Base Moves': ['Mudoon', 'Anti-Phys'], 'Learned Moves': [('Mazionga', 53),
                                                                                  ('Mana Drain', 54), ('Makakaja', 55),
                                                                                  ('Tarukaja', 56), ('Rakukaja', 57),
                                                                                  ('Sukukaja', 58)], 'Level': 52,
                         'Strength': 10, 'Magic': 20, 'Vitality': 18,
                         'Agility': 16, 'Luck': 8, 'Void': ['Death'], 'Resist': ['Phys'],
                         'Weaknesses': ['Force', 'Expel'], 'Race': 'Foul'},
              'Cu Chulainn': {'Learned Moves': [('Zandyne', 53), ('Thunderclap', 54), ('Charisma', 55),
                                                ('Blight', 56), ('Attack All', 57)], 'Level': 52, 'Strength': 21,
                              'Magic': 15, 'Vitality': 17, 'Agility': 14, 'Luck': 15, 'Reflect': ['Force'],
                              'Void': ['Expel'], 'Race': 'Genma'},
              'White Rider': {'Base Moves': ['Prominence', "God's Bow"], 'Learned Moves': [('Tetraja', 53),
                                                                                           ('Dekaja', 54),
                                                                                           ('Mana Aid', 55)],
                              'Level': 52, 'Strength': 23, 'Magic': 17,
                              'Vitality': 16, 'Agility': 18, 'Luck': 13, 'Absorb': ['Force'],
                              'Void': ['Fire', 'Expel', 'Death', 'Curse', 'Nerve', 'Mind'], 'Race': 'Fiend'},
              'Dominion': {'Base Moves': ['Violet Flash', 'Diarahan'], 'Learned Moves': [('Tetrakarn', 51),
                                                                                         ('Persuade', 52),
                                                                                         ('Makakaja', 53),
                                                                                         ('Makajam', 54),
                                                                                         ('Mahamaon', 55)], 'Level': 50,
                           'Strength': 15, 'Magic': 18, 'Vitality': 15, 'Agility': 11, 'Luck': 11,
                           'Reflect': ['Expel'], 'Weaknesses': ['Death', 'Curse'], 'Race': 'Divine'},
              'Titan': {'Base Moves': ['Guillotine', 'Taunt', 'Beseech'], 'Learned Moves': [('Stun Gaze', 50),
                                                                                            ('Life Surge', 51),
                                                                                            ('Retaliate', 52),
                                                                                            ('Fire Breath', 53)],
                        'Level': 49,
                        'Strength': 21, 'Magic': 10, 'Vitality': 17, 'Agility': 8, 'Luck': 13, 'Void': ['Force'],
                        'Weaknesses': ['Elec'], 'Race': 'Jirae'},
              'Legion': {'Base Moves': ['Deathtouch', 'Tetrakarn'], 'Learned Moves': [('Anti-Phys', 50),
                                                                                      ('Tempest', 51),
                                                                                      ('Hell Gaze', 52),
                                                                                      ('Pulinpa', 53),
                                                                                      ('Mamudoon', 54)], 'Level': 49,
                         'Strength': 19, 'Magic': 11, 'Vitality': 21, 'Agility': 9, 'Luck': 9,
                         'Reflect': ['Death'], 'Weaknesses': ['Elec', 'Expel'], 'Race': 'Haunt'},
              'Sati': {'Base Moves': ['Agidyne', 'Sexy Gaze', 'Recarm'], 'Learned Moves': [('Maragidyne', 49),
                                                                                           ('Makatora', 50),
                                                                                           ('Pester', 51),
                                                                                           ('Allure', 52)], 'Level': 48,
                       'Strength': 11,
                       'Magic': 20, 'Vitality': 13, 'Agility': 15, 'Luck': 17, 'Reflect': ['Expel'],
                       'Absorb': ['Fire'], 'Weaknesses': ['Ice'], 'Race': 'Lady', 'Evolution': ('Parvati', 52)},
              'Purski': {'Base Moves': ['Binding Cry', 'Watchful', 'Scout'], 'Learned Moves':
                  [('Stasis Blade', 49), ('Panic Voice', 50), ('Force Boost', 51), ('Chaos Blade', 52),
                   ('Mazandyne', 53)], 'Level': 48, 'Strength': 19, 'Magic': 15, 'Vitality': 17,
                         'Agility': 9, 'Luck': 12, 'Void': ['Force', 'Expel'], 'Weaknesses': ['Elec'],
                         'Race': 'Yoma', 'Evolution': ('Ganesha', 53)},
              'Atavaka': {'Base Moves': ['Mighty Gust', 'Might'], 'Learned Moves': [('Endure', 48),
                                                                                    ('Binding Cry', 49),
                                                                                    ('Retaliate', 50),
                                                                                    ('Chaos Blade', 51)], 'Level': 47,
                          'Strength': 24, 'Magic': 14, 'Vitality': 20, 'Agility': 10, 'Luck': 14,
                          'Reflect': ['Expel', 'Death'], 'Weaknesses': ['Nerve', 'Mind'], 'Race': 'Deity'},
              'Kaiwan': {'Base Moves': ['Charm Bite', 'Mudoon', 'Sonic Wave'], 'Learned Moves':
                  [('Sukukaja', 48), ('Trade', 49), ('Rakukaja', 50), ('Evil Gaze', 51),
                   ('Void Expel', 52)], 'Level': 47, 'Strength': 14, 'Magic': 19, 'Vitality': 19,
                         'Agility': 11, 'Luck': 8, 'Void': ['Death'], 'Resist': ['Fire', 'Ice', 'Elec', 'Force'],
                         'Weaknesses': ['Expel'], 'Race': 'Night'},
              'Oberon': {'Base Moves': ['Heat Wave', 'Mediarama', 'Wooing'], 'Learned Moves':
                  [('Makarakarn', 47), ('Diarahan', 48), ('Tornado', 49), ('Bufudyne', 50),
                   ('Ziodyne', 51)], 'Level': 46, 'Strength': 16, 'Magic': 19, 'Vitality': 13,
                         'Agility': 8, 'Luck': 10, 'Resist': ['Phys'], 'Weaknesses': ['Curse'], 'Race': 'Fairy'},
              'Hanuman': {'Learned Moves': [('Rakukaja', 47), ('Endure', 48), ('Kidnap', 49),
                                            ('Life Surge', 50)], 'Level': 46, 'Strength': 17, 'Magic': 12,
                          'Vitality': 15,
                          'Agility': 19, 'Luck': 13, 'Void': ['Expel'], 'Resist': 'Phys', 'Race': 'Genma',
                          'Evolution': ('Wu Kong', 50)},
              'Yatagarasu': {'Base Moves': ['Violet Flash', 'Mana Aid'], 'Learned Moves': [('Wind Cutter', 47),
                                                                                           ('Mana Gain', 48),
                                                                                           ('Force Boost', 49),
                                                                                           ('Recarmdra', 50)],
                             'Level': 46,
                             'Strength': 13, 'Magic': 18, 'Vitality': 12, 'Agility': 16, 'Luck': 10,
                             'Reflect': ['Force', 'Expel'], 'Race': 'Avatar'},
              'Mikazuchi': {'Base Moves': ['Shock', 'Ziodyne'], 'Learned Moves': [('Arbitration', 46),
                                                                                  ('Dark Sword', 47),
                                                                                  ('Life Refill', 48),
                                                                                  ('Mazionga', 49)], 'Level': 45,
                            'Strength': 21, 'Magic': 16, 'Vitality': 19, 'Agility': 11, 'Luck': 12,
                            'Reflect': ['Elec'], 'Void': ['Expel'], 'Weaknesses': ['Force'], 'Race': 'Kishin'},
              'Ose': {'Base Moves': ['Blight', 'Rakukaja', 'War Cry'], 'Learned Moves': [('Dekaja', 46),
                                                                                         ('Dekunda', 47),
                                                                                         ('Blackmail', 48),
                                                                                         ('Focus', 49),
                                                                                         ('Makarakarn', 50)],
                      'Level': 45,
                      'Strength': 17, 'Magic': 11, 'Vitality': 14, 'Agility': 12, 'Luck': 11,
                      'Void': ['Death'], 'Weaknesses': ['Nerve'], 'Race': 'Fallen'},
              'Pazuzu': {'Base Moves': ['Hell Gaze', 'Mediarama', 'Intimidate'], 'Learned Moves':
                  [('Void Force', 46), ('Arid Needle', 47), ('Tentarafoo', 48), ('Wet Wind', 49)],
                         'Level': 45, 'Strength': 16, 'Magic': 19, 'Vitality': 20, 'Agility': 10, 'Luck': 8,
                         'Void': ['Death'], 'Weaknesses': ['Ice'], 'Race': 'Vile'},
              'Sakahagi': {'Base Moves': ['Maragion', 'Mabufula', 'Mazionga', 'Mazanma', 'Panic Voice',
                                          'War Cry'], 'Learned Moves': [('Void Force', 46), ('Void Elec', 47)],
                           'Attack': {'Hits': 3}, 'Level': 45, 'Strength': 17, 'Magic': 17, 'Vitality': 15,
                           'Agility': 15, 'Luck': 11, 'Void': ['Expel', 'Death', 'Curse', 'Nerve', 'Mind'],
                           'Race': 'Foul'},
              'Dionysus': {'Base Moves': ['Maragion', 'Void Fire'], 'Learned Moves': [('Wine Party', 45),
                                                                                      ('Dismal Tune', 46),
                                                                                      ('Tempest', 47),
                                                                                      ('Maragidyne', 48)], 'Level': 44,
                           'Strength': 16, 'Magic': 20, 'Vitality': 15, 'Agility': 13, 'Luck': 15,
                           'Void': ['Fire', 'Expel', 'Death'], 'Weaknesses': ['Ice'], 'Race': 'Fury'},
              'Jinn': {'Base Moves': ['Mazanma', 'Zandyne', 'Force Boost'], 'Learned Moves': [('Diarama', 45),
                                                                                              ('Kamikaze', 46),
                                                                                              ('Flatter', 47),
                                                                                              ('Taunt', 48)],
                       'Level': 44, 'Strength': 14,
                       'Magic': 19, 'Vitality': 13, 'Agility': 14, 'Luck': 8, 'Absorb': ['Force'],
                       'Weaknesses': ['Nerve'], 'Race': 'Yoma', 'Evolution': ('Efreet', 48)},
              'Ikusa': {'Base Moves': ['Arid Needle', 'Petradi', 'Analyze'], 'Learned Moves': [('Begging', 45),
                                                                                               ('Dark Pledge', 46),
                                                                                               ('Mighty Gust', 47),
                                                                                               ('Mudoon', 48)],
                        'Level': 44, 'Strength': 17,
                        'Magic': 15, 'Vitality': 13, 'Agility': 9, 'Luck': 10, 'Void': ['Nerve'],
                        'Weaknesses': ['Force'], 'Race': 'Brute'},
              'Long': {'Learned Moves': [('Life Gain', 45), ('Stone Bite', 46), ('Ice Breath', 47),
                                         ('Violet Flash', 48)], 'Level': 44, 'Strength': 15, 'Magic': 13,
                       'Vitality': 22,
                       'Agility': 9, 'Luck': 11, 'Absorb': ['Ice'], 'Weaknesses': ['Fire'], 'Race': 'Dragon'},
              'Baihu': {'Base Moves': ['Stone Bite', 'Ice Breath', 'Life Aid'], 'Learned Moves':
                  [('Life Aid', 44), ('Might', 45), ('Beseech', 46), ('Focus', 47), ('Bufudyne', 48)],
                        'Level': 43, 'Strength': 19, 'Magic': 8, 'Vitality': 15, 'Agility': 17, 'Luck': 8,
                        'Void': ['Ice', 'Expel'], 'Weaknesses': ['Fire'], 'Race': 'Holy'},
              'Setanta': {'Base Moves': ['Guillotine', 'Sukukaja', 'Estoma'], 'Learned Moves':
                  [('Retaliate', 44), ('Taunt', 45), ('Void Curse', 46), ('Wooing', 47),
                   ('Tempest', 48)], 'Level': 43, 'Strength': 17, 'Magic': 12, 'Vitality': 20,
                          'Agility': 12, 'Luck': 6, 'Reflect': ['Force'], 'Weaknesses': ['Curse', 'Nerve'],
                          'Race': 'Fairy', 'Evolution': ('Cu Chulainn', 48)},
              'Yaksini': {'Base Moves': ['Guillotine', 'Riberama', 'Kidnap'], 'Learned Moves':
                  [('Binding Cry', 44), ('Void Ice', 45), ('Tentarafoo', 46), ('Retaliate', 47)],
                          'Level': 43, 'Strength': 17, 'Magic': 11, 'Vitality': 15, 'Agility': 11, 'Luck': 9,
                          'Void': ['Force'], 'Weaknesses': ['Elec'], 'Race': 'Femme'},
              'Mothman': {'Base Moves': ['Stun Claw', 'Evil Gaze'], 'Learned Moves': [('Trafuri', 44),
                                                                                      ('Panic Voice', 45),
                                                                                      ('Fire Breath', 46),
                                                                                      ('Void Elec', 47)], 'Level': 43,
                          'Strength': 11, 'Magic': 18, 'Vitality': 18, 'Agility': 8, 'Luck': 8,
                          'Void': ['Fire', 'Death'], 'Weaknesses': ['Elec'], 'Race': 'Wilder'},
              'Phantom': {'Base Moves': ['Last Resort', 'Mana Drain'], 'Learned Moves': [('Mazionga', 43),
                                                                                         ('Kamikaze', 44),
                                                                                         ('Tarunda', 45),
                                                                                         ('Dekaja', 46),
                                                                                         ('Ziodyne', 47)], 'Level': 42,
                          'Strength': 9, 'Magic': 17, 'Vitality': 14, 'Agility': 15, 'Luck': 7,
                          'Void': ['Death'], 'Resist': ['Phys'], 'Weaknesses': ['Force', 'Expel'],
                          'Race': 'Foul'},
              'Hell Biker': {'Base Moves': ['Hell Spin', 'Hell Burner'], 'Learned Moves': [('Hell Exhaust', 43),
                                                                                           ('Attack All', 44)],
                             'Level': 42, 'Strength': 17, 'Magic': 14, 'Vitality': 14,
                             'Agility': 17, 'Luck': 10, 'Absorb': ['Force'],
                             'Void': ['Fire', 'Expel', 'Death', 'Curse', 'Nerve', 'Mind'], 'Race': 'Fiend'},
              'Kushinada': {'Base Moves': ['Toxic Sting', 'Mediarama', 'Nag'], 'Learned Moves':
                  [('Maragion', 42), ('Paraladi', 43), ('Lucky Find', 44), ('Beseech', 45)],
                            'Level': 41, 'Strength': 12, 'Magic': 19, 'Vitality': 14, 'Agility': 10, 'Luck': 18,
                            'Reflect': ['Expel'], 'Weaknesses': ['Death'], 'Race': 'Lady'},
              'Virtue': {'Base Moves': ['Mahama', 'Mediarama', 'Detain'], 'Learned Moves': [('Arid Needle', 42),
                                                                                            ('Makarakarn', 43),
                                                                                            ('Mazionga', 44),
                                                                                            ('Thunderclap', 45)],
                         'Level': 41,
                         'Strength': 12, 'Magic': 17, 'Vitality': 17, 'Agility': 8, 'Luck': 7,
                         'Reflect': ['Expel'], 'Weaknesses': ['Force', 'Death'], 'Race': 'Divine'},
              'Okuninushi': {'Base Moves': ['Chaos Blade', 'Mamudo'], 'Learned Moves': [('Wooing', 40),
                                                                                        ('Agidyne', 41),
                                                                                        ('Makajamon', 42),
                                                                                        ('Beckon Call', 43)],
                             'Level': 39,
                             'Strength': 16, 'Magic': 16, 'Vitality': 13, 'Agility': 11, 'Luck': 10,
                             'Reflect': ['Expel'], 'Void': ['Death'], 'Race': 'Kishin'},
              'Horus': {'Base Moves': ['Mahama', 'Watchful'], 'Learned Moves': [('Mana Gain', 39),
                                                                                ('Dekunda', 40), ('Liftoma', 41),
                                                                                ('Mediarama', 42), ('Thunderclap', 43)],
                        'Level': 38,
                        'Strength': 12, 'Magic': 16, 'Vitality': 14, 'Agility': 21, 'Luck': 10,
                        'Reflect': ['Expel'], 'Resist': ['Phys'], 'Weaknesses': ['Death'], 'Race': 'Deity'},
              'Troll': {'Base Moves': ['Mutudi', 'Begging'], 'Learned Moves': [('Mabufula', 39),
                                                                               ('Berserk', 40), ('Life Gain', 40),
                                                                               ('Lightoma', 41), ('Diarahan', 42)],
                        'Level': 38,
                        'Strength': 14, 'Magic': 10, 'Vitality': 21, 'Agility': 4, 'Luck': 9, 'Absorb': ['Ice'],
                        'Weaknesses': ['Mind'], 'Race': 'Fairy'},
              'Kurama': {'Learned Moves': [('Violet Flash', 39), ('Force Boost', 40), ('Fog Breath', 41),
                                           ('Wind Cutter', 42), ('Starlight', 43)], 'Level': 38, 'Strength': 13,
                         'Magic': 17,
                         'Vitality': 13, 'Agility': 17, 'Luck': 8, 'Absorb': ['Force'], 'Void': ['Expel'],
                         'Race': 'Genma'},
              'Onkot': {'Base Moves': ['Berserk', 'Tarukaja', 'Might'], 'Learned Moves': [('Tetrakarn', 38),
                                                                                          ('Brutal Slash', 39),
                                                                                          ('Stone Hunt', 40),
                                                                                          ('Sukukaja', 41),
                                                                                          ('Sacrifice', 42)],
                        'Level': 37, 'Strength': 14, 'Magic': 9, 'Vitality': 11, 'Agility': 15, 'Luck': 12,
                        'Resist': ['Phys'], 'Weaknesses': ['Curse', 'Nerve'], 'Race': 'Yoma',
                        'Evolution': ('Hanuman', 42)},
              'Berith': {'Base Moves': ['Heat Wave', 'Mudo', 'Kidnap'], 'Learned Moves': [('Dekaja', 38),
                                                                                          ('Maragion', 39),
                                                                                          ('Dismal Tune', 40),
                                                                                          ('Fire Boost', 41),
                                                                                          ('Hellfire', 42)],
                         'Level': 37, 'Strength': 16, 'Magic': 10, 'Vitality': 17, 'Agility': 8, 'Luck': 8,
                         'Absorb': ['Fire'], 'Void': ['Death'], 'Resist': ['Phys'], 'Weaknesses': ['Ice'],
                         'Race': 'Fallen'},
              'Raja Naga': {'Base Moves': ['Tarukaja', 'Drain Attack'], 'Learned Moves': [('Counter', 38),
                                                                                          ('Shock', 39), ('Wooing', 40),
                                                                                          ('Tempest', 41),
                                                                                          ('Void Fire', 42)],
                            'Level': 37,
                            'Strength': 15, 'Magic': 9, 'Vitality': 21, 'Agility': 8, 'Luck': 9,
                            'Absorb': ['Elec'], 'Resist': ['Phys'], 'Weaknesses': ['Fire'], 'Race': 'Snake'},
              'Succubus': {'Base Moves': ['Dormina', 'Analyze', 'Nag'], 'Learned Moves': [('Eternal Rest', 38),
                                                                                          ('Sexy Gaze', 39),
                                                                                          ('Life Drain', 40),
                                                                                          ('Tentarafoo', 41)],
                           'Level': 37,
                           'Strength': 10, 'Magic': 16, 'Vitality': 11, 'Agility': 10, 'Luck': 10,
                           'Void': ['Mind'], 'Weaknesses': ['Expel'], 'Race': 'Night'},
              'Daisoujou': {'Base Moves': ['Mahamaon', 'Meditation'], 'Learned Moves': [('Mamudoon', 38),
                                                                                        ('Prayer', 39), ('Preach', 40)],
                            'Level': 37, 'Strength': 12, 'Magic': 21,
                            'Vitality': 11, 'Agility': 13, 'Luck': 10, 'Reflect': ['Death'],
                            'Absorb': ['Curse', 'Mind'], 'Void': ['Expel', 'Nerve'], 'Race': 'Fiend'},
              'Feng Huang': {'Base Moves': ['Fire Breath', 'Wing Buffet', 'Liftoma'], 'Learned Moves':
                  [('Recarm', 37), ('Arbitration', 38), ('Mazionga', 39), ('Life Aid', 40)],
                             'Level': 36, 'Strength': 10, 'Magic': 10, 'Vitality': 10, 'Agility': 17, 'Luck': 13,
                             'Absorb': ['Elec'], 'Void': ['Expel'], 'Weaknesses': ['Ice'], 'Race': 'Holy'},
              'Sarutahiko': {'Base Moves': ['Berserk', 'Lightoma'], 'Learned Moves': [('Haggle', 36),
                                                                                      ('Stone Gaze', 37),
                                                                                      ('Counter', 38), ('Focus', 39),
                                                                                      ('Hell Thrust', 40)],
                             'Level': 35, 'Strength': 18, 'Magic': 7, 'Vitality': 17, 'Agility': 7, 'Luck': 6,
                             'Void': ['Expel', 'Death'], 'Weaknesses': ['Nerve'], 'Race': 'Jirae'},
              'Saki Mitama': {'Base Moves': ['Dormina', 'Analyze', 'Trade'], 'Learned Moves':
                  [('Mazanma', 36), ('Mediarama', 37), ('Mazionga', 38), ('Tetrakarn', 39)],
                              'Level': 35, 'Strength': 10, 'Magic': 11, 'Vitality': 10, 'Agility': 11,
                              'Luck': 20, 'Void': ['Expel', 'Death', 'Curse', 'Nerve', 'Mind'],
                              'Resist': ['Fire', 'Ice', 'Elec', 'Force'], 'Race': 'Mitama'},
              'Mizuchi': {'Base Moves': ['Bufula', 'Mabufula', 'Makakaja'], 'Learned Moves':
                  [('Makarakarn', 35), ('Me Patra', 36), ('Berserk', 37), ('Fog Breath', 38)],
                          'Level': 34, 'Strength': 12, 'Magic': 13, 'Vitality': 19, 'Agility': 7, 'Luck': 7,
                          'Absorb': ['Elec'], 'Void': ['Ice', 'Expel'], 'Weaknesses': ['Fire'], 'Race': 'Snake',
                          'Evolution': ('Long', 38)},
              'Orthrus': {'Base Moves': ['Stun Claw', 'Fire Breath'], 'Learned Moves': [('Fire Boost', 35),
                                                                                        ('Scout', 36), ('War Cry', 37),
                                                                                        ('Hell Fang', 38)], 'Level': 24,
                          'Strength': 16,
                          'Magic': 8, 'Vitality': 13, 'Agility': 11, 'Luck': 6, 'Absorb': ['Fire'],
                          'Weaknesses': ['Ice'], 'Race': 'Beast'},
              'Komoku': {'Base Moves': ['Mighty Gust', 'Mazanma'], 'Learned Moves': [('Life Gain', 34),
                                                                                     ('Beseech', 35),
                                                                                     ('Mana Bonus', 36),
                                                                                     ('Tetraja', 37)], 'Level': 33,
                         'Strength': 16,
                         'Magic': 12, 'Vitality': 14, 'Agility': 9, 'Luck': 9, 'Reflect': ['Force'],
                         'Void': ['Expel'], 'Weaknesses': ['Elec'], 'Race': 'Kishin'},
              'Power': {'Base Moves': ['Tarukaja', 'Dark Might', 'Brainwash'], 'Learned Moves':
                  [('Guillotine', 34), ('Mahama', 35), ('Hamaon', 36), ('Void Nerve', 37)], 'Level': 33,
                        'Strength': 16, 'Magic': 8, 'Vitality': 16, 'Agility': 7, 'Luck': 6,
                        'Reflect': ['Expel'], 'Weaknesses': ['Death', 'Nerve'], 'Race': 'Divine'},
              'Baphomet': {'Base Moves': ['Makakaja', 'Beckon Call', 'Dark Pledge'], 'Learned Moves':
                  [('Evil Gaze', 34), ('Maragion', 35), ('Eternal Rest', 36), ('Dismal Tune', 37)],
                           'Level': 33, 'Strength': 8, 'Magic': 17, 'Vitality': 17, 'Agility': 9, 'Luck': 10,
                           'Reflect': ['Death'], 'Void': ['Expel'], 'Race': 'Vile'},
              'Valkyrie': {'Learned Moves': [('Guillotine', 34), ('Soul Recruit', 35), ('Counter', 36),
                                             ('Might', 37)], 'Level': 33, 'Strength': 15, 'Magic': 12, 'Vitality': 14,
                           'Agility': 12, 'Luck': 10, 'Absorb': ['Fire'], 'Void': ['Expel'], 'Race': 'Wargod'},
              'Shikome': {'Base Moves': ['Mazanma', 'Stone Gaze', 'Loan'], 'Learned Moves':
                  [('Anti-Death', 33), ('Sonic Wave', 34), ('Stun Needle', 35), ('Drain Attack', 36)],
                          'Level': 32, 'Strength': 8, 'Magic': 16, 'Vitality': 9, 'Agility': 10, 'Luck': 9,
                          'Void': ['Curse', 'Nerve'], 'Resist': ['Mind'], 'Weaknesses': ['Fire'],
                          'Race': 'Femme'},
              'Kusi Mitama': {'Base Moves': ['Dekaja', 'Sukukaja', 'Analyze'], 'Learned Moves':
                  [('Anti-Force', 33), ('Anti-Ice', 34), ('Anti-Elec', 35), ('Anti-Fire', 36)],
                              'Level': 32, 'Strength': 9, 'Magic': 18, 'Vitality': 8, 'Agility': 12, 'Luck': 12,
                              'Void': ['Expel', 'Death', 'Curse', 'Nerve', 'Mind'],
                              'Resist': ['Fire', 'Ice', 'Elec', 'Force'], 'Race': 'Mitama'},
              'Nue': {'Base Moves': ['Stun Claw', 'War Cry'], 'Learned Moves': [('Ice Breath', 32),
                                                                                ('Panic Voice', 33), ('Ice Boost', 34),
                                                                                ('Mamudo', 35)], 'Level': 31,
                      'Strength': 14,
                      'Magic': 9, 'Vitality': 12, 'Agility': 8, 'Luck': 8, 'Void': ['Ice', 'Death'],
                      'Weaknesses': ['Fire'], 'Race': 'Wilder'},
              'Sarasvati': {'Base Moves': ['Mute Gaze', 'Mana Refill'], 'Learned Moves': [('Recarm', 31),
                                                                                          ('Seduce', 32),
                                                                                          ('Mazanma', 33),
                                                                                          ('Force Boost', 34)],
                            'Level': 30, 'Strength': 9,
                            'Magic': 17, 'Vitality': 11, 'Agility': 9, 'Luck': 12,
                            'Void': ['Expel', 'Curse', 'Nerve', 'Mind'], 'Weaknesses': ['Fire'],
                            'Race': 'Megami'},
              'Arahabaki': {'Learned Moves': [('Mabufula', 31), ('Stone Gaze', 32), ('Mudo', 33),
                                              ('Panic Voice', 34), ('Drain Attack', 35)], 'Level': 30, 'Strength': 14,
                            'Magic': 10, 'Vitality': 19, 'Agility': 6, 'Luck': 9, 'Reflect': ['Ice'],
                            'Void': ['Phys', 'Expel', 'Death'], 'Weaknesses':
                                ['Fire', 'Elec', 'Force', 'Curse', 'Nerve', 'Mind'], 'Race': 'Vile'},
              'Gui Xian': {'Learned Moves': [('Bufula', 31), ('Estoma', 32), ('Ice Boost', 33),
                                             ('Ice Breath', 34)], 'Level': 30, 'Strength': 9, 'Magic': 11,
                           'Vitality': 16,
                           'Agility': 4, 'Luck': 10, 'Reflect': ['Expel'], 'Absorb': ['Ice'],
                           'Weaknesses': ['Elec'], 'Race': 'Dragon'},
              'Matador': {'Base Moves': ['Andalucia', 'Mazan'], 'Learned Moves': [('Dekunda', 31),
                                                                                  ('Focus', 32), ('Taunt', 33),
                                                                                  ('Red Capote', 34)], 'Level': 30,
                          'Strength': 12,
                          'Magic': 9, 'Vitality': 11, 'Agility': 19, 'Luck': 9,
                          'Void': ['Force', 'Expel', 'Death', 'Curse', 'Nerve', 'Mind'], 'Race': 'Fiend'},
              'Eligor': {'Base Moves': ['Hell Thrust', 'Rakukaja', 'Dark Might'], 'Learned Moves':
                  [('Mudo', 30), ('Berserk', 31), ('Riberama', 32), ('Intimidate', 33),
                   ('Stone Gaze', 34)], 'Level': 29, 'Strength': 14, 'Magic': 9, 'Vitality': 14,
                         'Agility': 6, 'Luck': 6, 'Void': ['Death'], 'Resist': ['Phys'], 'Weaknesses': ['Elec'],
                         'Race': 'Fallen'},
              'Nigi Mitama': {'Base Moves': ['Rakunda', 'Analyze', 'Persuade'], 'Learned Moves':
                  [('Fire Boost', 30), ('Ice Boost', 31), ('Elec Boost', 32), ('Force Boost', 33)],
                              'Level': 29, 'Strength': 10, 'Magic': 10, 'Vitality': 10, 'Agility': 16,
                              'Luck': 10, 'Void': ['Expel', 'Death', 'Curse', 'Nerve', 'Mind'],
                              'Resist': ['Fire', 'Ice', 'Elec', 'Force'], 'Race': 'Mitama'},
              'Karasu': {'Base Moves': ['Wing Buffet', 'Tarukaja'], 'Learned Moves': [('Mana Gain', 29),
                                                                                      ('Gonnection', 30),
                                                                                      ('Mahama', 31), ('Might', 32),
                                                                                      ('Tornado', 33)], 'Level': 28,
                         'Strength': 12, 'Magic': 11, 'Vitality': 11, 'Agility': 10, 'Luck': 8,
                         'Reflect': ['Force'], 'Weaknesses': ['Curse'], 'Race': 'Yoma',
                         'Evolution': ('Kurama', 33)},
              'Principality': {'Base Moves': ['Zanma', 'Bright Might', 'Gonnection'], 'Learned Moves':
                  [('Diarama', 29), ('Mana Bonus', 30), ('Hamaon', 31), ('Heat Wave', 32)],
                               'Level': 28, 'Strength': 11, 'Magic': 12, 'Vitality': 9, 'Agility': 7,
                               'Luck': 9, 'Void': ['Expel'], 'Weaknesses': ['Death'], 'Race': 'Divine'},
              'Naga': {'Base Moves': ['Tarukaja', 'Drain Attack', 'Trade'], 'Learned Moves': [('Life Gain', 29),
                                                                                              ('Fog Breath', 30),
                                                                                              ('Hell Thrust', 31),
                                                                                              ('Zionga', 32)],
                       'Level': 28, 'Strength': 13,
                       'Magic': 8, 'Vitality': 16, 'Agility': 7, 'Luck': 8, 'Absorb': ['Elec'],
                       'Weaknesses': ['Fire'], 'Race': 'Snake', 'Evolution': ('Raja Naga', 32)},
              'Pisaca': {'Base Moves': ['Venom Bite', 'Sukunda'], 'Learned Moves': [('Stun Gaze', 29),
                                                                                    ('Life Drain', 30),
                                                                                    ('Sonic Wave', 31), ('Dekunda', 32),
                                                                                    ('Mazionga', 33)],
                         'Level': 28, 'Strength': 8, 'Magic': 10, 'Vitality': 17, 'Agility': 7, 'Luck': 6,
                         'Void': ['Death', 'Curse', 'Mind'], 'Weaknesses': ['Fire'], 'Race': 'Haunt'},
              'Black Ooze': {'Base Moves': ['Charm Bite', 'Mute Gaze'], 'Learned Moves':
                  [('Last Resort', 29), ('Deathtouch', 30), ('Mana Drain', 31), ('Panic Voice', 32),
                   ('Anti-Expel', 33)], 'Level': 28, 'Strength': 11, 'Magic': 9, 'Vitality': 16,
                             'Agility': 6, 'Luck': 6, 'Void': ['Death'], 'Resist': ['Phys'],
                             'Weaknesses': ['Elec', 'Expel'], 'Race': 'Foul'},
              'Zouchou': {'Base Moves': ['Brutal Slash', 'Agilao', 'Mahama'], 'Learned Moves':
                  [('Detain', 28), ('Hamaon', 29), ('Anti-Death', 30), ('Might', 31)], 'Level': 27,
                          'Strength': 15, 'Magic': 10, 'Vitality': 12, 'Agility': 7, 'Luck': 10,
                          'Void': ['Expel', 'Curse', 'Nerve'], 'Weaknesses': ['Force'], 'Race': 'Kishin'},
              'Senri': {'Learned Moves': [('Mazanma', 28), ('Lucky Find', 29), ('Stone Hunt', 30),
                                          ('Drain Attack', 31)], 'Level': 27, 'Strength': 10, 'Magic': 14,
                        'Vitality': 9,
                        'Agility': 12, 'Luck': 9, 'Absorb': ['Force'], 'Void': ['Expel'],
                        'Weaknesses': ['Elec'], 'Race': 'Holy'},
              'Kelpie': {'Base Moves': ['Pulinpa', 'Paraladi', 'Arbitration'], 'Learned Moves':
                  [('Stun Bite', 27), ('Anti-Nerve', 28), ('Marin Karin', 29), ('Diarama', 30)],
                         'Level': 26, 'Strength': 9, 'Magic': 13, 'Vitality': 9, 'Agility': 8, 'Luck': 7,
                         'Resist': ['Ice'], 'Weaknesses': ['Force'], 'Race': 'Fairy'},
              'Cai-Zhi': {'Base Moves': ['Hell Thrust', 'Toxic Cloud', 'Mutudi'], 'Learned Moves':
                  [('Hamaon', 27), ('Scout', 28), ('Paraladi', 29), ('Mabufula', 30)], 'Level': 26,
                          'Strength': 13, 'Magic': 12, 'Vitality': 9, 'Agility': 9, 'Luck': 7,
                          'Void': ['Ice', 'Expel'], 'Weaknesses': ['Curse', 'Nerve', 'Mind'], 'Race': 'Avatar'},
              'Oni': {'Base Moves': ['Berserk', 'Rakunda', 'Haggle'], 'Learned Moves': [('War Cry', 26),
                                                                                        ('Estoma', 27), ('Begging', 28),
                                                                                        ('Life Gain', 29),
                                                                                        ('Dark Sword', 30)],
                      'Level': 25,
                      'Strength': 13, 'Magic': 7, 'Vitality': 12, 'Agility': 6, 'Luck': 7, 'Resist': ['Phys'],
                      'Weaknesses': ['Nerve'], 'Race': 'Brute'},
              'Incubus': {'Base Moves': ['Wing Buffet', 'Sexy Gaze', 'Flatter'], 'Learned Moves':
                  [('Stun Claw', 26), ('Wooing', 27), ('Evil Gaze', 28), ('Life Drain', 29)],
                          'Attack': {'Hits': 3}, 'Level': 25, 'Strength': 7, 'Magic': 14, 'Vitality': 8,
                          'Agility': 9, 'Luck': 7, 'Void': ['Curse', 'Mind'], 'Weaknesses': ['Force'],
                          'Race': 'Night'},
              'Raiju': {'Base Moves': ['Zionga', 'Lightoma'], 'Learned Moves': [('Feral Claw', 26),
                                                                                ('Shock', 27), ('Needle Rush', 28),
                                                                                ('Elec Boost', 29)], 'Level': 25,
                        'Strength': 8,
                        'Magic': 15, 'Vitality': 8, 'Agility': 8, 'Luck': 5, 'Absorb': ['Elec'],
                        'Void': ['Death'], 'Weaknesses': ['Force'], 'Race': 'Wilder'},
              'Ara Mitama': {'Base Moves': ['Tarukaja', 'Analyze', 'Bright Might'], 'Learned Moves':
                  [('Life Aid', 26), ('Life Refill', 27), ('Counter', 28), ('Lunge', 29)],
                             'Level': 25, 'Strength': 12, 'Magic': 10, 'Vitality': 10, 'Agility': 10,
                             'Luck': 10, 'Void': ['Expel', 'Death', 'Curse', 'Nerve', 'Mind'],
                             'Resist': ['Fire', 'Ice', 'Elec', 'Force'], 'Race': 'Mitama'},
              'Kikuri-Hime': {'Base Moves': ['Sexy Gaze', 'Diarama'], 'Learned Moves': [("Maiden's Plea", 25),
                                                                                        ('Posumudi', 26),
                                                                                        ('Me Patra', 27),
                                                                                        ('Recarm', 28)], 'Level': 24,
                              'Strength': 10, 'Magic': 16, 'Vitality': 11, 'Agility': 8, 'Luck': 11,
                              'Void': ['Expel', 'Curse', 'Nerve', 'Mind'], 'Weaknesses': ['Fire'],
                              'Race': 'Lady'},
              'Makami': {'Learned Moves': [('Void Mind', 25), ('Petradi', 26), ('Diarama', 27), ('Recarm', 28)],
                         'Level': 24, 'Strength': 11, 'Magic': 14, 'Vitality': 9, 'Agility': 7, 'Luck': 11,
                         'Reflect': ['Expel'], 'Void': ['Fire'], 'Race': 'Avatar'},
              'Dis': {'Base Moves': ['Agilao', 'Makajam', 'Tetraja'], 'Learned Moves': [('Diarama', 24),
                                                                                        ('Stone Gaze', 25),
                                                                                        ('Makatora', 26),
                                                                                        ('Me Patra', 27)], 'Level': 23,
                      'Strength': 10,
                      'Magic': 14, 'Vitality': 10, 'Agility': 7, 'Luck': 6, 'Void': ['Fire'], 'Race': 'Yoma',
                      'Evolution': ('Valkyrie', 27)},
              'Badb Catha': {'Base Moves': ['Needle Rush', 'Liftoma'], 'Learned Moves': [('Detain', 24),
                                                                                         ('Wing Buffet', 25),
                                                                                         ('Anti-Force', 26),
                                                                                         ('Mana Aid', 27)], 'Level': 23,
                             'Strength': 16, 'Magic': 8, 'Vitality': 13, 'Agility': 11, 'Luck': 6,
                             'Resist': ['Phys'], 'Weaknesses': ['Elec'], 'Race': 'Beast'},
              'Unicorn': {'Base Moves': ['Mabufu', 'Media', 'Rakukaja'], 'Learned Moves':
                  [('Life Refill', 22), ('Stun Bite', 23), ('Tetraja', 24), ('Me Patra', 25),
                   ('Diarama', 26)], 'Level': 21, 'Strength': 9, 'Magic': 12, 'Vitality': 10,
                          'Agility': 7, 'Luck': 7, 'Void': ['Expel', 'Curse', 'Mind'],
                          'Weaknesses': ['Elec'], 'Race': 'Holy'},
              'Forneus': {'Base Moves': ['Stun Bite', 'Riberama'], 'Learned Moves': [('Bufula', 21),
                                                                                     ('Loan', 22), ('Fog Breath', 23),
                                                                                     ('Anti-Elec', 24),
                                                                                     ('Mabufula', 25)],
                          'Level': 20, 'Strength': 10, 'Magic': 7, 'Vitality': 10, 'Agility': 5, 'Luck': 8,
                          'Void': ['Ice', 'Death'], 'Weaknesses': ['Elec'], 'Race': 'Fallen'},
              'Momunofu': {'Base Moves': ['Lunge', 'Focus'], 'Learned Moves': [('Life Bonus', 21),
                                                                               ('Brutal Slash', 22), ('Persuade', 23),
                                                                               ('Kamikaze', 24)], 'Level': 20,
                           'Strength': 13, 'Magic': 6, 'Vitality': 10, 'Agility': 7, 'Luck': 8,
                           'Resist': ['Phys'], 'Weaknesses': ['Curse', 'Nerve', 'Mind'], 'Race': 'Brute',
                           'Evolution': ('Arahabaki', 24)},
              'Taraka': {'Base Moves': ['Shibaboo', 'Taunt', 'Analyze'], 'Learned Moves': [('Rakukaja', 21),
                                                                                           ('Beseech', 22),
                                                                                           ('Kamikaze', 23),
                                                                                           ('Zionga', 24),
                                                                                           ('Heat Wave', 25)],
                         'Level': 20, 'Strength': 10, 'Magic': 6, 'Vitality': 11, 'Agility': 6, 'Luck': 7,
                         'Void': ['Nerve'], 'Weaknesses': ['Ice'], 'Race': 'Femme'},
              'Chatterskull': {'Base Moves': ['Stun Gaze', 'Sukunda'], 'Learned Moves': [('Dekaja', 21),
                                                                                         ('Dormina', 22),
                                                                                         ('Last Resort', 23),
                                                                                         ('Hell Thrust', 24)],
                               'Level': 20,
                               'Strength': 7, 'Magic': 12, 'Vitality': 6, 'Agility': 7, 'Luck': 8,
                               'Absorb': ['Fire'], 'Void': ['Death'], 'Weaknesses': ['Expel', 'Curse'],
                               'Race': 'Haunt'},
              'Flaemis': {'Base Moves': ['Maragi', 'Bright Might'], 'Learned Moves': [('Makakaja', 21),
                                                                                      ('Media', 22), ('Void Mind', 23),
                                                                                      ('Agilao', 24)], 'Level': 20,
                          'Strength': 10,
                          'Magic': 12, 'Vitality': 6, 'Agility': 6, 'Luck': 7, 'Absorb': ['Fire'],
                          'Void': ['Expel', 'Death'], 'Weaknesses': ['Ice'], 'Race': 'Element'},
              'Koppa': {'Base Moves': ['Wing Buffet', 'Tarukaja'], 'Learned Moves': [('Watchful', 20),
                                                                                     ('Shibaboo', 21), ('Makatora', 22),
                                                                                     ('Kamikaze', 23), ('Zanma', 24)],
                        'Level': 19,
                        'Strength': 10, 'Magic': 14, 'Vitality': 10, 'Agility': 7, 'Luck': 6,
                        'Void': ['Force'], 'Weaknesses': ['Curse'], 'Race': 'Yoma',
                        'Evolution': ('Karasu', 24)},
              'Pyro Jack': {'Base Moves': ['Agi', 'Maragi', 'Nag'], 'Learned Moves': [('Stun Gaze', 20),
                                                                                      ('Lunge', 21), ('Agilao', 22),
                                                                                      ('Anti-Ice', 23)], 'Level': 19,
                            'Strength': 8,
                            'Magic': 10, 'Vitality': 8, 'Agility': 6, 'Luck': 7, 'Void': ['Fire'],
                            'Weaknesses': ['Ice'], 'Race': 'Fairy'},
              'Uzume': {'Base Moves': ['Mazan', 'Media'], 'Learned Moves': [('Hama', 19), ('Seduce', 20),
                                                                            ('Petradi', 21), ('Life Bonus', 22),
                                                                            ('Mana Refill', 23)], 'Level': 18,
                        'Strength': 6, 'Magic': 12, 'Vitality': 8, 'Agility': 8, 'Luck': 12,
                        'Void': ['Force', 'Expel'], 'Weaknesses': ['Elec'], 'Race': 'Megami'},
              'Archangel': {'Base Moves': ['Mighty Gust', 'Tarukaja'], 'Learned Moves': [('Hama', 19),
                                                                                         ('Estoma', 20),
                                                                                         ('Wing Buffet', 21),
                                                                                         ('Persuade', 22),
                                                                                         ('Diarama', 23)],
                            'Level': 18, 'Strength': 11, 'Magic': 6, 'Vitality': 8, 'Agility': 7, 'Luck': 6,
                            'Reflect': ['Expel'], 'Weaknesses': ['Ice', 'Death'], 'Race': 'Divine'},
              'Nekomata': {'Base Moves': ['Stun Needle', 'Marin Karin', 'Paraladi'], 'Learned Moves':
                  [('Mana Bonus', 19), ('Feral Claw', 20), ('Pester', 21), ('Mute Gaze', 22)],
                           'Level': 18, 'Strength': 7, 'Magic': 12, 'Vitality': 8, 'Agility': 7, 'Luck': 7,
                           'Absorb': ['Force'], 'Weaknesses': ['Elec'], 'Race': 'Beast',
                           'Evolution': ('Senri', 22)},
              'Fomor': {'Base Moves': ['Bufu', 'Lullaby'], 'Learned Moves': [('Lunge', 19), ('Life Bonus', 20),
                                                                             ('Kidnap', 21), ('Mabufu', 22),
                                                                             ('Berserk', 23)], 'Level': 18,
                        'Strength': 8,
                        'Magic': 7, 'Vitality': 14, 'Agility': 4, 'Luck': 5, 'Void': ['Ice'],
                        'Weaknesses': ['Elec'], 'Race': 'Night'},
              'Minakata': {'Base Moves': ['Mazio', 'Zionga', 'Dark Might'], 'Learned Moves':
                  [('Makajam', 18), ('Intimidate', 19), ('Stun Gaze', 20), ('Dekaja', 21),
                   ('Focus', 22)], 'Level': 17, 'Strength': 11, 'Magic': 8, 'Vitality': 11,
                           'Agility': 9, 'Luck': 5, 'Reflect': ['Elec'], 'Void': ['Expel'],
                           'Weaknesses': ['Fire', 'Nerve'], 'Race': 'Kishin'},
              'Yaka': {'Base Moves': ['Deathtouch', 'Tarunda'], 'Learned Moves': [('Mazio', 18),
                                                                                  ('Taunt', 18), ('Dia', 19),
                                                                                  ('Venom Claw', 20), ('Diarama', 21)],
                       'Level': 17,
                       'Strength': 8, 'Magic': 10, 'Vitality': 8, 'Agility': 5, 'Luck': 6, 'Void': ['Death'],
                       'Weaknesses': ['Ice', 'Expel'], 'Race': 'Haunt'},
              'Blob': {'Base Moves': ['Last Resort', 'Tarunda'], 'Learned Moves': [('Toxic Sting', 17),
                                                                                   ('Marin Karin', 18),
                                                                                   ('Mana Drain', 19), ('Zanma', 20)],
                       'Level': 16, 'Strength': 8,
                       'Magic': 6, 'Vitality': 10, 'Agility': 5, 'Luck': 7, 'Void': ['Death'],
                       'Resist': ['Phys'], 'Weaknesses': ['Ice', 'Expel'], 'Race': 'Foul'},
              'Bicorn': {'Base Moves': ['Charm Bite', 'Sukukaja'], 'Learned Moves': [('Maragi', 16),
                                                                                     ('Bright Might', 17),
                                                                                     ('Anti-Nerve', 18),
                                                                                     ('Pulinpa', 19),
                                                                                     ('Stun Gaze', 20)],
                         'Level': 15, 'Strength': 10, 'Magic': 6, 'Vitality': 10, 'Agility': 5, 'Luck': 4,
                         'Void': ['Death'], 'Resist': ['Curse', 'Nerve', 'Mind'], 'Weaknesses': ['Elec'],
                         'Race': 'Wilder'},
              'Aquans': {'Base Moves': ['Sukukaja', 'Anti-Expel'], 'Learned Moves': [('Mabufu', 16),
                                                                                     ('Anti-Nerve', 17),
                                                                                     ('Life Bonus', 18),
                                                                                     ('Bufula', 19)], 'Level': 15,
                         'Strength': 6, 'Magic': 10, 'Vitality': 6, 'Agility': 6, 'Luck': 8,
                         'Reflect': ['Ice'], 'Void': ['Expel', 'Death'], 'Weaknesses': ['Fire'],
                         'Race': 'Element'},
              'Isora': {'Base Moves': ['Venom Bite', 'Analyze'], 'Learned Moves': [('Kidnap', 15),
                                                                                   ('Lullaby', 16), ('Ice Breath', 17),
                                                                                   ('Media', 18)], 'Level': 14,
                        'Strength': 9,
                        'Magic': 8, 'Vitality': 8, 'Agility': 6, 'Luck': 3, 'Resist': ['Ice'],
                        'Weaknesses': ['Fire'], 'Race': 'Yoma'},
              'Nozuchi': {'Base Moves': ['Lunge', 'Toxic Cloud'], 'Learned Moves': [('Counter', 15),
                                                                                    ('Flatter', 16), ('Rakukaja', 17),
                                                                                    ('Sacrifice', 18)], 'Level': 14,
                          'Strength': 11,
                          'Magic': 6, 'Vitality': 10, 'Agility': 4, 'Luck': 7, 'Absorb': ['Force'],
                          'Weaknesses': ['Elec'], 'Race': 'Snake', 'Evolution': ('Gui Xian', 18)},
              'Shiisaa': {'Base Moves': ['Feral Claw', 'Shock'], 'Learned Moves': [('War Cry', 14),
                                                                                   ('Brainwash', 15),
                                                                                   ('Stone Bite', 16), ('Counter', 17),
                                                                                   ('Anti-Fire', 18)],
                          'Level': 13, 'Strength': 9, 'Magic': 6, 'Vitality': 7, 'Agility': 9, 'Luck': 6,
                          'Absorb': ['Elec'], 'Void': ['Expel'], 'Weaknesses': ['Fire'], 'Race': 'Holy'},
              'Inugami': {'Base Moves': ['Feral Bite', 'Fire Breath'], 'Learned Moves': [('Media', 14),
                                                                                         ('Rakunda', 15),
                                                                                         ('Fog Breath', 16),
                                                                                         ('Panic Voice', 17)],
                          'Level': 13,
                          'Strength': 10, 'Magic': 7, 'Vitality': 9, 'Agility': 6, 'Luck': 5,
                          'Void': ['Fire', 'Death'], 'Weaknesses': ['Force'], 'Race': 'Beast',
                          'Evolution': ('Makami', 17)},
              'Sudama': {'Base Moves': ['Zan', 'Begging'], 'Learned Moves': [('Mazan', 14), ('Kamikaze', 15),
                                                                             ('Makatora', 16), ('Makakaja', 17),
                                                                             ('Sukukaja', 18)], 'Level': 13,
                         'Strength': 7,
                         'Magic': 7, 'Vitality': 3, 'Agility': 8, 'Luck': 8, 'Resist': ['Force'],
                         'Weaknesses': ['Fire'], 'Race': 'Jirae'},
              'Angel': {'Base Moves': ['Hama', 'Dia'], 'Learned Moves': [('Detain', 12), ('Patra', 13),
                                                                         ('Petradi', 14), ('Stun Needle', 15),
                                                                         ('Life Aid', 16)], 'Level': 11, 'Strength': 4,
                        'Magic': 7, 'Vitality': 7, 'Agility': 7, 'Luck': 6, 'Void': ['Expel'],
                        'Weaknesses': ['Force', 'Death'], 'Race': 'Divine'},
              'Choronzon': {'Base Moves': ['Agi', 'Sukunda'], 'Learned Moves': [('Fire Breath', 12),
                                                                                ('Berserk', 13), ('Trafuri', 14),
                                                                                ('Stone Gaze', 15)], 'Level': 11,
                            'Strength': 9, 'Magic': 4, 'Vitality': 15, 'Agility': 1, 'Luck': 2,
                            'Absorb': ['Fire'], 'Void': ['Death'], 'Resist': ['Phys'],
                            'Weaknesses': ['Force', 'Expel'], 'Race': 'Haunt'},
              'High Pixie': {'Base Moves': ['Zio', 'Wing Buffet'], 'Learned Moves': [('Paraladi', 11),
                                                                                     ('Me Patra', 12), ('Seduce', 13),
                                                                                     ('Lucky Find', 14),
                                                                                     ('Trafuri', 15)],
                             'Level': 10, 'Strength': 4, 'Magic': 6, 'Vitality': 4, 'Agility': 6, 'Luck': 10,
                             'Resist': ['Elec'], 'Race': 'Fairy', 'Evolution': ('Queen Mab', 16)},
              'Aeros': {'Base Moves': ['Zio', 'Dia'], 'Learned Moves': [('Lullaby', 12), ('Marin Karin', 13),
                                                                        ('Anti-Mind', 14), ('Toxic Sting', 15)],
                        'Level': 11, 'Strength': 5, 'Magic': 8,
                        'Vitality': 6, 'Agility': 8, 'Luck': 5, 'Void': ['Expel', 'Death'],
                        'Resist': ['Phys', 'Fire', 'Ice', 'Elec', 'Force'], 'Race': 'Element'},
              'Apsaras': {'Base Moves': ['Lullaby', 'Mutudi', 'Seduce'], 'Learned Moves': [('Mazio', 9),
                                                                                           ('Anti-Mind', 10),
                                                                                           ('Makajam', 11),
                                                                                           ('Dormina', 12)], 'Level': 8,
                          'Strength': 6,
                          'Magic': 6, 'Vitality': 6, 'Agility': 5, 'Luck': 5, 'Absorb': ['Elec'],
                          'Weaknesses': ['Fire'], 'Race': 'Yoma'},
              'Lilim': {'Base Moves': ['Sexy Gaze', 'Rakunda'], 'Learned Moves': [('Analyze', 9),
                                                                                  ('Dark Pledge', 10), ('Tarunda', 11),
                                                                                  ('Mazio', 12)], 'Level': 8,
                        'Strength': 4,
                        'Magic': 8, 'Vitality': 5, 'Agility': 7, 'Luck': 4, 'Void': ['Elec'],
                        'Weaknesses': ['Ice'], 'Race': 'Night', 'Evolution': ('Lilith', 12)},
              'Jack Frost': {'Base Moves': ['Bufu', 'Dark Might', 'Gonnection'], 'Learned Moves':
                  [('Mabufu', 8), ('Trade', 9), ('Ice Breath', 10), ('Life Refill', 11)],
                             'Level': 7, 'Strength': 5, 'Magic': 8, 'Vitality': 6, 'Agility': 4, 'Luck': 4,
                             'Absorb': ['Ice'], 'Weaknesses': ['Fire'], 'Race': 'Fairy'},
              'Datsue-Ba': {'Base Moves': ['Needle Rush', 'Shibaboo'], 'Learned Moves': [('Haggle', 8),
                                                                                         ('Bufu', 9), ('Patra', 10),
                                                                                         ('Dormina', 11)], 'Level': 7,
                            'Strength': 4,
                            'Magic': 8, 'Vitality': 4, 'Agility': 5, 'Luck': 6, 'Void': ['Nerve', 'Mind'],
                            'Weaknesses': ['Elec'], 'Race': 'Femme'},
              'Mou-Ryo': {'Base Moves': ['Toxic Sting', 'Pulinpa'], 'Learned Moves': [('Zan', 8),
                                                                                      ('Deathtouch', 9),
                                                                                      ('Mana Refill', 10),
                                                                                      ('Mazan', 11)], 'Level': 7,
                          'Strength': 6,
                          'Magic': 7, 'Vitality': 4, 'Agility': 5, 'Luck': 5, 'Void': ['Death'],
                          'Weaknesses': ['Expel'], 'Race': 'Foul'},
              'Erthys': {'Base Moves': ['Zio', 'Patra'], 'Learned Moves': [('Rakukaja', 8),
                                                                           ('Anti-Curse', 9), ('Arbitration', 10),
                                                                           ('Mazio', 11)], 'Level': 7, 'Strength': 6,
                         'Magic': 5, 'Vitality': 8, 'Agility': 4, 'Luck': 5, 'Void': ['Expel', 'Death'],
                         'Weaknesses': ['Force'], 'Race': 'Element'},
              'Zhen': {'Base Moves': ['Mute Gaze', 'Posumudi'], 'Learned Moves': [('Toxic Sting', 7),
                                                                                  ('War Cry', 8), ('Wing Buffet', 9),
                                                                                  ('Mazan', 10), ('Void Nerve', 11)],
                       'Level': 6,
                       'Strength': 4, 'Magic': 6, 'Vitality': 6, 'Agility': 5, 'Luck': 5,
                       'Void': ['Death'], 'Resist': ['Curse', 'Nerve', 'Mind'], 'Weaknesses': ['Fire'],
                       'Race': 'Wilder'},
              'Slime': {'Base Moves': ['Feral Bite', 'Deathtouch'], 'Learned Moves': [('Sukunda', 7),
                                                                                      ('Last Resort', 8),
                                                                                      ('War Cry', 9),
                                                                                      ('Sonic Wave', 10)], 'Level': 6,
                        'Strength': 6,
                        'Magic': 5, 'Vitality': 3, 'Agility': 5, 'Luck': 7, 'Void': ['Death'],
                        'Resist': ['Phys'], 'Weaknesses': ['Fire', 'Ice', 'Elec', 'Force', 'Expel'],
                        'Race': 'Foul'},
              'Hua Po': {'Base Moves': ['Agi', 'Pester'], 'Learned Moves': [('Patra', 6), ('Nag', 7),
                                                                            ('Sexy Gaze', 8), ('Rakukaja', 9),
                                                                            ('Maragi', 10)], 'Level': 5, 'Strength': 4,
                         'Magic': 5, 'Vitality': 5, 'Agility': 6, 'Luck': 5, 'Resist': ['Fire'],
                         'Weaknesses': ['Ice'], 'Race': 'Jirae'},
              'Shikigami': {'Base Moves': ['Zio', 'Beseech'], 'Learned Moves': [('Tarunda', 5),
                                                                                ('Sukunda', 6), ('Anti-Curse', 7),
                                                                                ('Tarukaja', 8)], 'Level': 4,
                            'Strength': 5,
                            'Magic': 5, 'Vitality': 4, 'Agility': 5, 'Luck': 5, 'Reflect': ['Elec'],
                            'Weaknesses': ['Fire'], 'Race': 'Brute'},
              'Preta': {'Base Moves': ['Feral Claw', 'Sukukaja'], 'Learned Moves': [('Agi', 5),
                                                                                    ('Deathtouch', 6),
                                                                                    ('Venom Claw', 7),
                                                                                    ('Fog Breath', 8)], 'Level': 4,
                        'Strength': 5,
                        'Magic': 4, 'Vitality': 5, 'Agility': 6, 'Luck': 4, 'Void': ['Death'],
                        'Weaknesses': ['Fire', 'Ice', 'Elec', 'Force', 'Expel'], 'Race': 'Haunt'},
              'Kodama': {'Base Moves': ['Zan', 'Gonnection'], 'Learned Moves': [('Dia', 4), ('Lunge', 5),
                                                                                ('Scout', 6), ('Anti-Force', 7)],
                         'Level': 3, 'Strength': 4, 'Magic': 4,
                         'Vitality': 4, 'Agility': 6, 'Luck': 5, 'Resist': ['Force'], 'Weaknesses': ['Fire'],
                         'Race': 'Jirae'},
              'Pixie': {'Base Moves': ['Zio', 'Dia'], 'Learned Moves': [('Seduce', 3), ('Rakunda', 4),
                                                                        ('Posumudi', 5), ('Wing Buffet', 6)],
                        'Level': 2, 'Strength': 3, 'Magic': 6,
                        'Vitality': 4, 'Agility': 2, 'Luck': 7, 'Resist': ['Elec'], 'Race': 'Fairy',
                        'Evolution': ('High Pixie', 6)},
              "Will o' Wisp": {'Base Moves': ['Needle Rush'], 'Learned Moves': [('Zan', 2), ('Riberama', 3),
                                                                                ('Deathtouch', 4), ('Last Resort', 5),
                                                                                ('Makakaja', 6)], 'Level': 1,
                               'Strength': 4, 'Magic': 5, 'Vitality': 4, 'Agility': 5, 'Luck': 3,
                               'Void': ['Death'], 'Resist': ['Phys'],
                               'Weaknesses': ['Fire', 'Ice', 'Elec', 'Force', 'Expel'], 'Race': 'Foul'}
              }


# In[6]:


magatama_dict = {'Masakados': {'Moves': [('Radiance', 1), ('Megidolaon', 1), ('Fire Repel', 1),
                                         ('Ice Repel', 1), ('Elec Repel', 1), ('Force Repel', 1),
                                         ('Phys Repel', 1)],
                               'Strength': 10,
                               'Magic': 10,
                               'Vitality': 10,
                               'Agility': 10,
                               'Luck': 0,
                               'Reflect': [],
                               'Absorb': [],
                               'Void': ['Phys', 'Fire', 'Ice', 'Elec', 'Force', 'Expel', 'Death', 'Curse',
                                        'Nerve', 'Mind'],
                               'Resist': [],
                               'Weaknesses': [],
                               'Alignment': 'Neutral'
                               },
                 'Kailash': {'Moves': [('Makarakarn', 72), ('Megido', 75), ('Tetrakarn', 78),
                                       ('Freikugel', 80), ('Megidola', 84)], 'Strength': 2, 'Magic': 10,
                             'Vitality': 5, 'Agility': 1, 'Luck': 2, 'Alignment': 'Neutral'},
                 'Gundari': {'Moves': [('Wind Cutter', 64), ('Force Drain', 66), ('Spiral Viper', 72)],
                             'Strength': 4, 'Magic': 1, 'Vitality': 2, 'Agility': 9, 'Luck': 3,
                             'Absorb': ['Force'], 'Weaknesses': ['Elec'], 'Alignment': 'Dark'},
                 'Gaea': {'Moves': [('Deathbound', 61), ('Avenge', 69), ('Gaea Rage', 74), ('Attack All', 76)],
                          'Strength': 10, 'Magic': 0, 'Vitality': 10, 'Agility': 0, 'Luck': 0,
                          'Resist': ['Phys'], 'Weaknesses': ['Force', 'Death', 'Expel'],
                          'Alignment': 'Dark'},
                 'Adama': {'Moves': [('Bolt Storm', 60), ('Mana Surge', 62), ('Elec Drain', 67)],
                           'Strength': 3, 'Magic': 2, 'Vitality': 8, 'Agility': 2, 'Luck': 2,
                           'Reflect': ['Elec'], 'Resist': ['Expel', 'Death'], 'Weaknesses': ['Force'],
                           'Alignment': 'Light'},
                 'Satan': {'Moves': [('Jive Talk', 51), ('Void Death', 55), ('Mana Aid', 58), ('Charisma', 60),
                                     ('Deadly Fury', 65)], 'Strength': 2, 'Magic': 8, 'Vitality': 1, 'Agility': 1,
                           'Luck': 4, 'Weaknesses': ['Expel'], 'Void': ['Death'], 'Alignment': 'Dark'},
                 'Vimana': {'Moves': [('Endure', 50), ('Tempest', 59), ('Javelin Rain', 68), ('Life Surge', 71),
                                      ('Hades Blast', 73)], 'Strength': 7, 'Magic': 1, 'Vitality': 3, 'Agility': 2,
                            'Luck': 5, 'Void': ['Nerve'], 'Alignment': 'Neutral'},
                 'Muspell': {'Moves': [('Tentarafoo', 49), ('Makajamon', 53), ('Xeros Beat', 56)],
                             'Strength': 0, 'Magic': 8, 'Vitality': 7, 'Agility': 0, 'Luck': 0,
                             'Resist': ['Nerve', 'Mind'], 'Alignment': 'Neutral'},
                 'Kamurogi': {'Moves': [('Blight', 45), ('Life Gain', 46), ('Iron Claw', 48), ('Retaliate', 54),
                                        ('Oni-Kagura', 64)], 'Strength': 8, 'Magic': 0, 'Vitality': 0, 'Agility': 4,
                              'Luck': 4, 'Resist': ['Expel', 'Death', 'Phys'],
                              'Weaknesses': ['Fire', 'Ice', 'Elec', 'Force'], 'Alignment': 'Light'},
                 'Sophia': {'Moves': [('Thunderclap', 45), ('Samarecarm', 57), ('Drain Attack', 59),
                                      ('Mediarahan', 63), ('Holy Wrath', 70)], 'Strength': 1, 'Magic': 2, 'Vitality': 5,
                            'Agility': 7, 'Luck': 4, 'Void': ['Expel'], 'Resist': ['Death'],
                            'Alignment': 'Light'},
                 'Djed': {'Moves': [('Tarukaja', 42), ('Sukukaja', 43), ('Makakaja', 44), ('Rakukaja', 45),
                                    ('Dekaja', 46)], 'Strength': 2, 'Magic': 6, 'Vitality': 2, 'Agility': 2, 'Luck': 2,
                          'Resist': ['Expel', 'Death'], 'Alignment': 'Dark'},
                 'Geis': {'Moves': [('Diarama', 37), ('Life Refill', 39), ('Tetraja', 41), ('Mediarama', 44),
                                    ('Diarahan', 47), ('Mana Refill', 51)], 'Strength': 2, 'Magic': 2, 'Vitality': 4,
                          'Agility': 4, 'Luck': 4, 'Void': ['Expel'], 'Alignment': 'Light'},
                 'Murakumo': {'Moves': [('Void Mind', 34), ('Void Nerve', 37), ('Chaos Blade', 40),
                                        ('Void Curse', 42)], 'Strength': 4, 'Magic': 4, 'Vitality': 1, 'Agility': 4,
                              'Luck': 1, 'Resist': ['Phys'], 'Weaknesses': ['Fire', 'Ice'],
                              'Alignment': 'Neutral'},
                 'Gehenna': {'Moves': [('Hellfire', 33), ('Void Fire', 42), ('Mana Gain', 45),
                                       ('Fire Drain', 60), ('Magma Axis', 65)], 'Strength': 3, 'Magic': 3,
                             'Vitality': 3,
                             'Agility': 3, 'Luck': 3, 'Absorb': ['Fire'], 'Weaknesses': ['Ice'],
                             'Alignment': 'Neutral'},
                 'Nirvana': {'Moves': [('Violet Flash', 32), ('Anti-Expel', 33), ('Divine Shot', 41),
                                       ('Void Expel', 56)], 'Strength': 1, 'Magic': 1, 'Vitality': 2, 'Agility': 2,
                             'Luck': 8, 'Void': ['Expel'], 'Weaknesses': ['Death'], 'Alignment': 'Light'},
                 'Miasma': {'Moves': [('Wild Dance', 31), ('Void Ice', 45), ('Glacial Blast', 52),
                                      ('Ice Drain', 60)], 'Strength': 2, 'Magic': 5, 'Vitality': 2, 'Agility': 2,
                            'Luck': 2, 'Void': ['Ice'], 'Weaknesses': ['Fire'], 'Alignment': 'Dark'},
                 'Anathema': {'Moves': [('Mana Drain', 28), ('Anti-Death', 32), ('Mamudo', 35),
                                        ('Evil Gaze', 38), ('Mamudoon', 49)], 'Strength': 0, 'Magic': 8,
                              'Vitality': 2, 'Agility': 1, 'Luck': 1, 'Void': ['Death'], 'Weaknesses': ['Expel'],
                              'Alignment': 'Dark'},
                 'Narukami': {'Moves': [('Shock', 21), ('Elec Boost', 26), ('Anti-Elec', 30), ('Void Elec', 44)],
                              'Strength': 5, 'Magic': 6, 'Vitality': 0, 'Agility': 0, 'Luck': 0,
                              'Void': ['Elec'], 'Weaknesses': ['Ice'], 'Alignment': 'Light'},
                 'Kamudo': {'Moves': [('Heat Wave', 18), ('Focus', 23), ("Mind's Eye", 25), ('Might', 29)],
                            'Strength': 5, 'Magic': 0, 'Vitality': 2, 'Agility': 3, 'Luck': 0,
                            'Resist': ['Phys'], 'Weaknesses': ['Curse', 'Nerve', 'Mind'],
                            'Alignment': 'Neutral'},
                 'Hifumi': {'Moves': [('Tornado', 17), ('Force Boost', 22), ('War Cry', 24), ('Anti-Force', 27),
                                      ('Void Force', 40)], 'Strength': 0, 'Magic': 3, 'Vitality': 0, 'Agility': 4,
                            'Luck': 3, 'Void': ['Force'], 'Weaknesses': ['Fire'], 'Alignment': 'Neutral'},
                 'Iyomante': {'Moves': [('Tarunda', 10), ('Sukunda', 13), ('Rakunda', 16), ('Life Aid', 36)],
                              'Strength': 2, 'Magic': 2, 'Vitality': 2, 'Agility': 2, 'Luck': 3,
                              'Void': ['Mind'], 'Alignment': 'Light'},
                 'Shiranui': {'Moves': [('Fire Breath', 9), ('Fire Boost', 14), ('Taunt', 19),
                                        ('Anti-Fire', 23)], 'Strength': 0, 'Magic': 5, 'Vitality': 0, 'Agility': 4,
                              'Luck': 0, 'Void': ['Fire'], 'Weaknesses': ['Force'], 'Alignment': 'Dark'},
                 'Wadatsumi': {'Moves': [('Ice Breath', 7), ('Mana Bonus', 11), ('Ice Boost', 15),
                                         ('Fog Breath', 21), ('Anti-Ice', 24)], 'Strength': 0, 'Magic': 3,
                               'Vitality': 2,
                               'Agility': 2, 'Luck': 1, 'Void': ['Ice'], 'Weaknesses': ['Elec'],
                               'Alignment': 'Neutral'},
                 'Ankh': {'Moves': [('Dia', 5), ('Fast Retreat', 12), ('Media', 19)], 'Strength': 1,
                          'Magic': 1, 'Vitality': 4, 'Agility': 0, 'Luck': 2, 'Void': ['Expel'],
                          'Weaknesses': ['Death'], 'Alignment': 'Light'},
                 'Marogareh': {'Moves': [('Lunge', 3), ('Analyze', 2), ('Life Bonus', 6), ('Berserk', 10),
                                         ('Counter', 20)], 'Strength': 2, 'Magic': 1, 'Vitality': 2,
                               'Agility': 1, 'Luck': 1, 'Alignment': 'Dark'}
                 }
# pierce listed in demon class; random chance of being given to any demifiend


# In[7]:


master_list = ['Demi-Fiend'] + list(demon_dict.keys()) + list(magatama_dict.keys())


# In[8]:


# sorted by element-?
# for random attacks: hits = max possible
# for others: hits = hits
# mandatory: category, target
# optional: element, hits, power, correction, limit, accuracy, MP, HP, special effect/chance, crit, damage calc
# note: default accuracy is 'None' (always hit), not 100
# only phys moves need "damage calc"
# "Heal" uses power/makakaja of user; "MP Recover" is only percentage (float) or finite amount (int)

# for recarm effects: use keyword "dead" (as opposed to "stock" for summon/beckon call)

# need shatter percentage
moves_dict = {'Attack': {'Category': 'Physical',
                         'Element': 'Phys',
                         'Target': 'Single Enemy',
                         'Hits': 1,
                         'Power': 32,
                         'Correction': 'None',
                         'Limit': 'None',
                         'Accuracy': 97,
                         'MP': 0,
                         'HP': 0,
                         'Special Effects': {},
                         'Crit': 4,
                         'Damage Calc': 'Level'},
              'Feral Bite': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 44,
                             'Accuracy': 76, 'HP': 12, 'Crit': 24, 'Damage Calc': 'Level'},
              'Feral Claw': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 34,
                             'Accuracy': 75, 'HP': 6, 'Crit': 25, 'Damage Calc': 'Level'},
              'Lunge': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 41,
                        'Accuracy': 76, 'HP': 10, 'Crit': 24, 'Damage Calc': 'Level'},
              'Needle Rush': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 41,
                              'Accuracy': 76, 'HP': 10, 'Crit': 24, 'Damage Calc': 'Level'},
              'Hell Thrust': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 47,
                              'Accuracy': 67, 'HP': 12, 'Crit': 33, 'Damage Calc': 'Level'},
              'Toxic Sting': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 31,
                              'Accuracy': 76, 'HP': 7, 'Special Effects': {'Poison': {'Accuracy': 40,
                                                                                      'Element': 'Curse'}}, 'Crit': 24,
                              'Damage Calc': 'Level'},
              'Venom Bite': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 41,
                             'Accuracy': 76, 'HP': 18, 'Special Effects': {'Poison': {'Accuracy': 40,
                                                                                      'Element': 'Curse'}}, 'Crit': 24,
                             'Damage Calc': 'Level'},
              'Venom Claw': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 41,
                             'Accuracy': 76, 'HP': 18, 'Special Effects': {'Poison': {'Accuracy': 40,
                                                                                      'Element': 'Curse'}}, 'Crit': 24,
                             'Damage Calc': 'Level'},
              'Charm Bite': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 41,
                             'Accuracy': 76, 'HP': 18, 'Special Effects': {'Charm': {'Accuracy': 55,
                                                                                     'Element': 'Mind'}}, 'Crit': 24,
                             'Damage Calc': 'Level'},
              'Mighty Gust': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 53,
                              'Accuracy': 74, 'HP': 14, 'Crit': 26, 'Damage Calc': 'HP'},
              'Stun Claw': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 44,
                            'Accuracy': 70, 'HP': 17, 'Special Effects': {'Stun': {'Accuracy': 40,
                                                                                   'Element': 'Nerve'}}, 'Crit': 30,
                            'Damage Calc': 'Level'},
              'Stun Needle': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 31,
                              'Accuracy': 76, 'HP': 7, 'Special Effects': {'Stun': {'Accuracy': 40,
                                                                                    'Element': 'Nerve'}}, 'Crit': 24,
                              'Damage Calc': 'Level'},
              'Berserk': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Random Enemies', 'Hits': 5,
                          'Power': 16, 'Accuracy': 97, 'HP': 13, 'Crit': 13, 'Damage Calc': 'Level'},
              'Brutal Slash': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 50,
                               'Accuracy': 74, 'HP': 13, 'Crit': 26, 'Damage Calc': 'HP'},
              'Stun Bite': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 44,
                            'Accuracy': 74, 'HP': 17, 'Special Effects': {'Stun': {'Accuracy': 40,
                                                                                   'Element': 'Nerve'}}, 'Crit': 26,
                            'Damage Calc': 'Level'},
              'Arid Needle': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 31,
                              'Accuracy': 74, 'HP': 12, 'Special Effects': {'Stone': {'Accuracy': 60,
                                                                                      'Element': 'Death'}}, 'Crit': 26,
                              'Damage Calc': 'Level'},
              'Guillotine': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 47,
                             'Accuracy': 67, 'HP': 17, 'Crit': 33, 'Damage Calc': 'HP'},
              'Iron Claw': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 56,
                            'Accuracy': 55, 'HP': 15, 'Crit': 45, 'Damage Calc': 'Level'},
              'Stone Bite': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 44,
                             'Accuracy': 74, 'HP': 22, 'Special Effects': {'Stone': {'Accuracy': 50,
                                                                                     'Element': 'Death'}}, 'Crit': 26,
                             'Damage Calc': 'Level'},
              'Heat Wave': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'All Enemies', 'Power': 19,
                            'Accuracy': 93, 'HP': 19, 'Crit': 26, 'Damage Calc': 'Level'},
              'Dark Sword': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 53,
                             'Accuracy': 60, 'HP': 22, 'Special Effects': {'Mute': {'Accuracy': 40,
                                                                                    'Element': 'Curse'}}, 'Crit': 40,
                             'Damage Calc': 'HP'},
              'Hell Fang': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 56,
                            'Accuracy': 55, 'HP': 15, 'Crit': 45, 'Damage Calc': 'Level'},
              'Tempest': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'All Enemies', 'Power': 31,
                          'Accuracy': 70, 'HP': 25, 'Crit': 30, 'Damage Calc': 'HP'},
              'Stasis Blade': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 53,
                               'Accuracy': 60, 'HP': 22, 'Special Effects': {'Bind': {'Accuracy': 65,
                                                                                      'Element': 'Nerve'}}, 'Crit': 40,
                               'Damage Calc': 'HP'},
              'Blight': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'All Enemies', 'Power': 22,
                         'Accuracy': 91, 'HP': 22, 'Special Effects': {'Poison': {'Accuracy': 20,
                                                                                  'Element': 'Curse'}}, 'Crit': 36,
                         'Damage Calc': 'HP'},
              'Chaos Blade': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Random Enemies', 'Hits': 5,
                              'Power': 22, 'Accuracy': 95, 'HP': 32, 'Special Effects': {'Panic':
                                                                                             {'Accuracy': 30,
                                                                                              'Element': 'Mind'}},
                              'Crit': 20, 'Damage Calc': 'HP'},
              'Deathbound': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Random Enemies', 'Hits': 5,
                             'Power': 38, 'Accuracy': 95, 'HP': 25, 'Crit': 21, 'Damage Calc': 'HP'},
              'Hades Blast': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'All Enemies', 'Power': 41,
                              'Accuracy': 90, 'HP': 32, 'Crit': 43, 'Damage Calc': 'Level'},
              'Hassohappa': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'All Enemies', 'Power': 47,
                             'Accuracy': 89, 'HP': 35, 'Crit': 46, 'Damage Calc': 'HP'},
              'Andalucia': {'Category': 'Physical', 'Elemnt': 'Phys', 'Target': 'All Enemies', 'Hits': 4,
                            'Power': 8, 'Accuracy': 100, 'HP': 6, 'Crit': 1, 'Damage Calc': 'Level'},
              'Boogie-Woogie': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Hits': 4,
                                'Power': 8, 'Accuracy': 97, 'MP': 3, 'Crit': 13, 'Damage Calc': 'Level'},
              'Deadly Fury': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'All Enemies', 'Power': 41,
                              'Accuracy': 97, 'HP': 32, 'Crit': 50, 'Damage Calc': 'Level'},
              'Divine Shot': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy', 'Power': 50,
                              'Accuracy': 97, 'HP': 13, 'Crit': 55, 'Damage Calc': 'Level'},
              'Earthquake': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'All Enemies', 'Power': 70,
                             'Accuracy': 90, 'HP': 45, 'Damage Calc': 'Level'},
              'Gaea Rage': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'All Enemies', 'Power': 47,
                            'Accuracy': 97, 'HP': 35, 'Crit': 30, 'Damage Calc': 'Level'},
              'Hell Spin': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'All Enemies', 'Power': 31,
                            'Accuracy': 95, 'HP': 25, 'Crit': 5, 'Damage Calc': 'Level'},
              'Javelin Rain': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'All Enemies',
                               'Power': 41, 'Accuracy': 97, 'HP': 40, 'Special Effects':
                                   {'Mute': {'Accuracy': 20, 'Element': 'Curse'}}, 'Crit': 30,
                               'Damage Calc': 'Level'},
              'Mokoi Boomerang': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'All Enemies',
                                  'Power': 25, 'MP': 10, 'Special Effects': {'Panic':
                                                                                 {'Accuracy': 30, 'Element': 'Mind'}},
                                  'Crit': 4, 'Damage Calc': 'Level'},
              'Oni-Kagura': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'All Enemies',
                             'Power': 38, 'Accuracy': 97, 'HP': 30, 'Crit': 30, 'Damage Calc': 'Level'},
              'Spiral Viper': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy',
                               'Power': 62, 'Accuracy': 97, 'HP': 18, 'Crit': 30, 'Damage Calc': 'Level'},
              'Terrorblade': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Random Enemies', 'Hits': 5,
                              'Power': 30, 'Accuracy': 97, 'MP': 10, 'Special Effects':
                                  {'Panic': {'Accuracy': 30, 'Element': 'Mind'}}, 'Crit': 4, 'Damage Calc': 'Level'},
              'Xeros Beat': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'All Enemies',
                             'Power': 37, 'Accuracy': 97, 'HP': 40, 'Special Effects':
                                 {'Bind': {'Accuracy': 30, 'Element': 'Nerve'}}, 'Crit': 30,
                             'Damage Calc': 'Level'},
              'Yoshitsune Show-Up': {'Category': 'Physical', 'Element': 'Phys', 'Target': 'Single Enemy',
                                     'Power': 36, 'Accuracy': 98, 'HP': 9, 'Crit': 50, 'Damage Calc': 'Level'},
              'Freikugel': {'Category': 'Physical', 'Element': 'Almighty', 'Target': 'Single Enemy',
                            'Power': 65, 'Accuracy': 97, 'HP': 17, 'Crit': 30, 'Damage Calc': 'Level'},
              'Tekisatsu': {'Category': 'Physical', 'Element': 'Almighty', 'Target': 'Single Enemy',
                            'Power': 40, 'Accuracy': 96, 'HP': 12, 'Special Effects': {'Kill': {'Accuracy': 40}},
                            'Crit': 4, 'Damage Calc': 'Level'},
              'Agi': {'Category': 'Magic', 'Element': 'Fire', 'Target': 'Single Enemy', 'Power': 37,
                      'Correction': 10, 'Limit': 104, 'Accuracy': 100, 'MP': 3},
              'Agilao': {'Category': 'Magic', 'Element': 'Fire', 'Target': 'Single Enemy', 'Power': 55,
                         'Correction': 16, 'Limit': 155, 'Accuracy': 100, 'MP': 6},
              'Maragi': {'Category': 'Magic', 'Element': 'Fire', 'Target': 'All Enemies', 'Power': 30,
                         'Correction': 9, 'Limit': 85, 'Accuracy': 100, 'MP': 8},
              'Fire Breath': {'Category': 'Magic', 'Element': 'Fire', 'Target': 'Random Enemies', 'Hits': 5,
                              'Power': 30, 'Correction': 8, 'Limit': 85, 'Accuracy': 100, 'MP': 9},
              'Agidyne': {'Category': 'Magic', 'Element': 'Fire', 'Target': 'Single Enemy', 'Power': 75,
                          'Correction': 20, 'Limit': 220, 'Accuracy': 100, 'MP': 10},
              'Hellfire': {'Category': 'Magic', 'Element': 'Fire', 'Target': 'Random Enemies', 'Hits': 4,
                           'Power': 50, 'Correction': 14, 'Limit': 140, 'Accuracy': 100, 'MP': 20},
              'Maragion': {'Category': 'Magic', 'Element': 'Fire', 'Target': 'All Enemies', 'Power': 45,
                           'Correction': 13, 'Limit': 126, 'Accuracy': 100, 'MP': 15},
              'Maragidyne': {'Category': 'Magic', 'Element': 'Fire', 'Target': 'All Enemies', 'Power': 65,
                             'Correction': 19, 'Limit': 183, 'Accuracy': 100, 'MP': 25},
              'Prominence': {'Category': 'Magic', 'Element': 'Fire', 'Target': 'Random Enemies', 'Hits': 4,
                             'Power': 90, 'Correction': 26, 'Limit': 253, 'Accuracy': 100, 'MP': 30},
              'Hell Burner': {'Category': 'Magic', 'Element': 'Fire', 'Target': 'All Enemies', 'Power': 30,
                              'Correction': 9, 'Limit': 85, 'Accuracy': 100, 'MP': 8},
              'Magma Axis': {'Category': 'Magic', 'Element': 'Fire', 'Target': 'Single Enemy', 'Power': 48,
                             'Correction': 14, 'Limit': 470, 'Accuracy': 100, 'HP': 15},
              'Ragnarok': {'Category': 'Magic', 'Element': 'Fire', 'Target': 'Single Enemy', 'Power': 80,
                           'Correction': 20, 'Limit': 800, 'Accuracy': 100, 'MP': 30},
              'Bufu': {'Category': 'Magic', 'Element': 'Ice', 'Target': 'Single Enemy', 'Power': 30,
                       'Correction': 9, 'Limit': 85, 'Accuracy': 100, 'MP': 3, 'Special Effects':
                           {'Freeze': {'Accuracy': 20}}},
              'Bufula': {'Category': 'Magic', 'Element': 'Ice', 'Target': 'Single Enemy', 'Power': 45,
                         'Correction': 13, 'Limit': 126, 'Accuracy': 100, 'MP': 6, 'Special Effects':
                             {'Freeze': {'Accuracy': 25}}},
              'Mabufu': {'Category': 'Magic', 'Element': 'Ice', 'Target': 'All Enemies', 'Power': 20,
                         'Correction': 6, 'Limit': 56, 'Accuracy': 100, 'MP': 8,
                         'Special Effects': {'Freeze': {'Accuracy': 10}}},
              'Ice Breath': {'Category': 'Magic', 'Element': 'Ice', 'Target': 'Random Enemies', 'Hits': 5,
                             'Power': 25, 'Correction': 7, 'Limit': 70, 'Accuracy': 100, 'MP': 9,
                             'Special Effects': {'Freeze': {'Accuracy': 17}}},
              'Bufudyne': {'Category': 'Magic', 'Element': 'Ice', 'Target': 'Single Enemy', 'Power': 65,
                           'Correction': 19, 'Limit': 183, 'Accuracy': 100, 'MP': 10, 'Special Effects':
                               {'Freeze': {'Accuracy': 30}}},
              'Mabufula': {'Category': 'Magic', 'Element': 'Ice', 'Target': 'All Enemies', 'Power': 35,
                           'Correction': 10, 'Limit': 98, 'Accuracy': 100, 'MP': 15,
                           'Special Effects': {'Freeze': {'Accuracy': 13}}},
              'Glacial Blast': {'Category': 'Magic', 'Element': 'Ice', 'Target': 'Random Enemies', 'Hits': 4,
                                'Power': 65, 'Correction': 19, 'Limit': 183, 'Accuracy': 100, 'MP': 25,
                                'Special Effects': {'Freeze': {'Accuracy': 15}}},
              'Mabufudyne': {'Category': 'Magic', 'Element': 'Ice', 'Target': 'All Enemies', 'Power': 55,
                             'Correction': 16, 'Limit': 155, 'Accuracy': 100, 'MP': 25,
                             'Special Effects': {'Freeze': {'Accuracy': 15}}},
              'Zio': {'Category': 'Magic', 'Element': 'Elec', 'Target': 'Single Enemy', 'Power': 30,
                      'Correction': 9, 'Limit': 85, 'Accuracy': 100, 'MP': 3, 'Special Effects':
                          {'Shock': {'Accuracy': 20}}},
              'Zionga': {'Category': 'Magic', 'Element': 'Elec', 'Target': 'Single Enemy', 'Power': 45,
                         'Correction': 13, 'Limit': 126, 'Accuracy': 100, 'MP': 6, 'Special Effects':
                             {'Shock': {'Accuracy': 25}}},
              'Mazio': {'Category': 'Magic', 'Element': 'Elec', 'Target': 'All Enemies', 'Power': 20,
                        'Correction': 6, 'Limit': 56, 'Accuracy': 100, 'MP': 8,
                        'Special Effects': {'Shock': {'Accuracy': 10}}},
              'Shock': {'Category': 'Magic', 'Element': 'Elec', 'Target': 'Random Enemies', 'Hits': 5,
                        'Power': 25, 'Correction': 5, 'Limit': 70, 'Accuracy': 100, 'MP': 9, 'Special Effects':
                            {'Shock': {'Accuracy': 17}}},
              'Mazionga': {'Category': 'Magic', 'Element': 'Elec', 'Target': 'All Enemies', 'Power': 35,
                           'Correction': 10, 'Limit': 98, 'Accuracy': 100, 'MP': 15,
                           'Special Effects': {'Shock': {'Accuracy': 13}}},
              'Ziodyne': {'Category': 'Magic', 'Element': 'Elec', 'Target': 'Single Enemy', 'Power': 65,
                          'Correction': 19, 'Limit': 183, 'Accuracy': 100, 'MP': 10, 'Special Effects':
                              {'Shock': {'Accuracy': 30}}},
              'Bolt Storm': {'Category': 'Magic', 'Element': 'Elec', 'Target': 'Random Enemies', 'Hits': 4,
                             'Power': 65, 'Correction': 19, 'Limit': 183, 'Accuracy': 100, 'MP': 25,
                             'Special Effects': {'Shock': {'Accuracy': 15}}},
              'Maziodyne': {'Category': 'Magic', 'Element': 'Elec', 'Target': 'All Enemies', 'Power': 55,
                            'Correction': 16, 'Limit': 155, 'Accuracy': 100, 'MP': 25,
                            'Special Effects': {'Shock': {'Accuracy': 15}}},
              'Mishaguji Thunder': {'Category': 'Magic', 'Element': 'Elec', 'Target': 'All Enemies', 'Power': 55,
                                    'Correction': 16, 'Limit': 155, 'Accuracy': 100, 'MP': 25,
                                    'Special Effects': {'Shock': {'Accuracy': 15}}},
              'Zan': {'Category': 'Magic', 'Element': 'Force', 'Target': 'Single Enemy', 'Power': 37,
                      'Correction': 10, 'Limit': 104, 'Accuracy': 100, 'MP': 3},
              'Zanma': {'Category': 'Magic', 'Element': 'Force', 'Target': 'Single Enemy', 'Power': 55,
                        'Correction': 16, 'Limit': 155, 'Accuracy': 100, 'MP': 6},
              'Mazan': {'Category': 'Magic', 'Element': 'Force', 'Target': 'All Enemies', 'Power': 30,
                        'Correction': 9, 'Limit': 84, 'Accuracy': 100, 'MP': 8},
              'Wing Buffet': {'Category': 'Magic', 'Element': 'Force', 'Target': 'Random Enemies', 'Hits': 5,
                              'Power': 30, 'Correction': 10, 'Limit': 84, 'Accuracy': 100, 'MP': 9},
              'Mazanma': {'Category': 'Magic', 'Element': 'Force', 'Target': 'All Enemies', 'Power': 40,
                          'Correction': 11, 'Limit': 112, 'Accuracy': 100, 'MP': 15},
              'Tornado': {'Category': 'Magic', 'Element': 'Force', 'Target': 'Random Enemies', 'Hits': 4,
                          'Power': 65, 'Correction': 19, 'Limit': 183, 'Accuracy': 100, 'MP': 25},
              'Zandyne': {'Category': 'Magic', 'Element': 'Force', 'Target': 'Single Enemy', 'Power': 75,
                          'Correction': 20, 'Limit': 220, 'Accuracy': 100, 'MP': 10},
              'Wind Cutter': {'Category': 'Magic', 'Element': 'Force', 'Target': 'Single Enemy', 'Power': 90,
                              'Correction': 26, 'Limit': 330, 'Accuracy': 100, 'MP': 13},
              'Mazandyne': {'Category': 'Magic', 'Element': 'Force', 'Target': 'All Enemies', 'Power': 65,
                            'Correction': 19, 'Limit': 183, 'Accuracy': 100, 'MP': 25},
              'Hell Exhaust': {'Category': 'Magic', 'Element': 'Force', 'Target': 'All Enemies', 'Power': 40,
                               'Correction': 11, 'Limit': 112, 'Accuracy': 100, 'MP': 15,
                               'Special Effects': {'Dekaja': {'Element': 'None'}}},
              'Hitokoto Gust': {'Category': 'Magic', 'Element': 'Force', 'Target': 'All Enemies', 'Power': 65,
                                'Correction': 19, 'Limit': 183, 'Accuracy': 100, 'MP': 25},
              'Wet Wind': {'Category': 'Magic', 'Element': 'Force', 'Target': 'All Enemies', 'Power': 65,
                           'Correction': 20, 'Limit': 200, 'Accuracy': 100, 'MP': 25,
                           'Special Effects': {'Stun': {'Accuracy': 20, 'Element': 'Nerve'}}},
              'Hama': {'Category': 'Magic', 'Element': 'Expel', 'Target': 'Single Enemy', 'Accuracy': 100,
                       'MP': 6, 'Special Effects': {'Kill': {'Accuracy': 40}}},
              'Hamaon': {'Category': 'Magic', 'Element': 'Expel', 'Target': 'Single Enemy', 'Accuracy': 100,
                         'MP': 10, 'Special Effects': {'Kill': {'Accuracy': 60}}},
              'Mahama': {'Category': 'Magic', 'Element': 'Expel', 'Target': 'All Enemies', 'Accuracy': 100,
                         'MP': 15, 'Special Effects': {'Kill': {'Accuracy': 20}}},
              'Thunderclap': {'Category': 'Magic', 'Element': 'Expel', 'Target': 'Single Enemy', 'Accuracy': 100,
                              'MP': 12, 'Special Effects': {'Reduce HP': {'Value': 0.5}}},
              'Violet Flash': {'Category': 'Magic', 'Element': 'Expel', 'Target': 'Single Enemy', 'Power': 75,
                               'Correction': 20, 'Limit': 220, 'Accuracy': 100, 'MP': 10},
              'Mahamaon': {'Category': 'Magic', 'Element': 'Expel', 'Target': 'All Enemies', 'Accuracy': 100,
                           'MP': 25, 'Special Effects': {'Kill': {'Accuracy': 30}}},
              'Holy Wrath': {'Category': 'Magic', 'Element': 'Expel', 'Target': 'All Enemies', 'Accuracy': 100,
                             'MP': 36, 'Special Effects': {'Reduce HP': {'Value': 0.5}}},
              'Radiance': {'Category': 'Magic', 'Element': 'Expel', 'Target': 'All Enemies', 'Power': 75,
                           'Correction': 21, 'Limit': 211, 'Accuracy': 100, 'MP': 30},
              "God's Bow": {'Category': 'Magic', 'Element': 'Expel', 'Target': 'Single Enemy', 'MP': 20,
                            'Special Effects': {'Kill': {}}},
              'Godly Light': {'Category': 'Magic', 'Element': 'Expel', 'Target': 'All Enemies', 'Accuracy': 100,
                              'MP': 10, 'Special Effects': {'Reduce HP': {'Value': 0.2}}},
              'Starlight': {'Category': 'Magic', 'Element': 'Expel', 'Target': 'All Enemies', 'Power': 50,
                            'Correction': 14, 'Limit': 140, 'Accuracy': 100, 'MP': 22},
              'Mudo': {'Category': 'Magic', 'Element': 'Death', 'Target': 'Single Enemy', 'Accuracy': 100,
                       'MP': 6, 'Special Effects': {'Kill': {'Accuracy': 40}}},
              'Mamudo': {'Category': 'Magic', 'Element': 'Death', 'Target': 'All Enemies', 'Accuracy': 100,
                         'MP': 15, 'Special Effects': {'Kill': {'Accuracy': 20}}},
              'Mudoon': {'Category': 'Magic', 'Element': 'Death', 'Target': 'Single Enemy', 'Accuracy': 100,
                         'MP': 10, 'Special Effects': {'Kill': {'Accuracy': 60}}},
              'Stone Gaze': {'Category': 'Magic', 'Element': 'Death', 'Target': 'Single Enemy', 'Accuracy': 100,
                             'MP': 6, 'Special Effects': {'Stone': {'Accuracy': 50}}},
              'Evil Gaze': {'Category': 'Magic', 'Element': 'Death', 'Target': 'Single Enemy', 'Accuracy': 55,
                            'MP': 8, 'Special Effects': {'One HP': {}}},
              'Hell Gaze': {'Category': 'Magic', 'Element': 'Death', 'Target': 'Single Enemy', 'Accuracy': 100,
                            'MP': 10, 'Special Effects': {'Kill': {'Accuracy': 70}}},
              'Mamudoon': {'Category': 'Magic', 'Element': 'Death', 'Target': 'All Enemies', 'Accuracy': 100,
                           'MP': 25, 'Special Effects': {'Kill': {'Accuracy': 30}}},
              'Mute Gaze': {'Category': 'Magic', 'Element': 'Curse', 'Target': 'Single Enemy', 'Accuracy': 100,
                            'MP': 5, 'Special Effects': {'Mute': {'Accuracy': 40}}},
              'Toxic Cloud': {'Category': 'Magic', 'Element': 'Curse', 'Target': 'All Enemies', 'Power': 25,
                              'Correction': 7, 'Limit': 70, 'Accuracy': 100, 'MP': 8, 'Special Effects':
                                  {'Poison': {'Accuracy': 20}}},
              'Makajam': {'Category': 'Magic', 'Element': 'Curse', 'Target': 'Single Enemy', 'Accuracy': 100,
                          'MP': 4, 'Special Effects': {'Mute': {'Accuracy': 40}}},
              'Dismal Tune': {'Category': 'Magic', 'Element': 'Curse', 'Target': 'All Enemies', 'Power': 55,
                              'Correction': 16, 'Limit': 155, 'Accuracy': 100, 'MP': 30, 'Special Effects':
                                  {'Mute': {'Accuracy': 15}}},
              'Makajamon': {'Category': 'Magic', 'Element': 'Curse', 'Target': 'All Enemies', 'Accuracy': 100,
                            'MP': 11, 'Special Effects': {'Mute': {'Accuracy': 20}}},
              'Soul Divide': {'Category': 'Magic', 'Element': 'Curse', 'Target': 'All Enemies', 'Accuracy': 100,
                              'MP': 30, 'Special Effects': {'Reduce HP': {'Value': 0.5},
                                                            'Mute': {'Accuracy': 30}}},
              'Shibaboo': {'Category': 'Magic', 'Element': 'Nerve', 'Target': 'Single Enemy', 'Accuracy': 100,
                           'MP': 5, 'Special Effects': {'Bind': {'Accuracy': 65}}},
              'Stun Gaze': {'Category': 'Magic', 'Element': 'Nerve', 'Target': 'Single Enemy', 'Accuracy': 100,
                            'MP': 5, 'Special Effects': {'Stun': {'Accuracy': 40}}},
              'Binding Cry': {'Category': 'Magic', 'Element': 'Nerve', 'Target': 'All Enemies', 'Accuracy': 100,
                              'MP': 14, 'Special Effects': {'Bind': {'Accuracy': 20}}},
              'Pulinpa': {'Category': 'Magic', 'Element': 'Mind', 'Target': 'Single Enemy', 'Accuracy': 100,
                          'MP': 5, 'Special Effects': {'Panic': {'Accuracy': 60}}},
              'Sexy Gaze': {'Category': 'Magic', 'Element': 'Mind', 'Target': 'Single Enemy', 'Accuracy': 100,
                            'MP': 5, 'Special Effects': {'Charm': {'Accuracy': 55}}},
              'Dormina': {'Category': 'Magic', 'Element': 'Mind', 'Target': 'All Enemies', 'Accuracy': 100,
                          'MP': 9, 'Special Effects': {'Sleep': {'Accuracy': 30}}},
              'Marin Karin': {'Category': 'Magic', 'Element': 'Mind', 'Target': 'Single Enemy', 'Accuracy': 100,
                              'MP': 5, 'Special Effects': {'Charm': {'Accuracy': 55}}},
              'Sonic Wave': {'Category': 'Magic', 'Element': 'Mind', 'Target': 'All Enemies', 'Accuracy': 100,
                             'MP': 9, 'Special Effects': {'Panic': {'Accuracy': 20}}},
              'Eternal Rest': {'Category': 'Magic', 'Element': 'Mind', 'Target': 'All Enemies', 'Accuracy': 100,
                               'MP': 16, 'Special Effects': {'Kill': {'Condition': 'Target Asleep'}}},
              'Panic Voice': {'Category': 'Magic', 'Element': 'Mind', 'Target': 'All Enemies', 'Accuracy': 100,
                              'MP': 8, 'Special Effects': {'Panic': {'Accuracy': 30}}},
              'Allure': {'Category': 'Magic', 'Element': 'Mind', 'Target': 'All Enemies', 'Accuracy': 100,
                         'MP': 13, 'Special Effects': {'Charm': {'Accuracy': 45}}},
              'Tentarafoo': {'Category': 'Magic', 'Element': 'Mind', 'Target': 'All Enemies', 'Power': 50,
                             'Correction': 16, 'Limit': 155, 'Accuracy': 100, 'MP': 15, 'Special Effects':
                                 {'Panic': {'Accuracy': 20}}},
              'Death Lust': {'Category': 'Magic', 'Element': 'Mind', 'Target': 'All Enemies', 'Power': 50,
                             'Correction': 16, 'Limit': 155, 'Accuracy': 100, 'MP': 15, 'Special Effects':
                                 {'Charm': {'Accuracy': 20}}},
              'Intoxicate': {'Category': 'Magic', 'Element': 'Mind', 'Target': 'All Enemies', 'Accuracy': 100,
                             'MP': 15, 'Special Effects': {'Charm': {'Accuracy': 60}}},
              'Preach': {'Category': 'Magic', 'Element': 'Mind', 'Target': 'All Enemies', 'Power': 20,
                         'Correction': 16, 'Limit': 155, 'Accuracy': 100, 'MP': 15, 'Special Effects':
                             {'Sleep': {'Accuracy': 40 / 3}, 'Panic': {'Accuracy': 40 / 3},
                              'Charm': {'Accuracy': 40 / 3}}},
              'Wild Dance': {'Category': 'Magic', 'Element': 'Mind', 'Target': 'All Enemies', 'Accuracy': 100,
                             'MP': 18, 'Special Effects': {'Panic': {'Accuracy': 65}}},
              'Deathtouch': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'Single Enemy', 'Power': 30,
                             'Correction': 10, 'Limit': 84, 'Accuracy': 100, 'MP': 5, 'Special Effects':
                                 {'HP Drain': {'Value': 1}}},
              'Mana Drain': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'Single Enemy', 'Power': 15,
                             'Correction': 4, 'Limit': 42, 'Accuracy': 100, 'MP': 2, 'Special Effects':
                                 {'MP Drain': {'Value': 1}}},
              'Life Drain': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'Single Enemy', 'Power': 30,
                             'Correction': 8, 'Limit': 84, 'Accuracy': 100, 'MP': 10, 'Special Effects':
                                 {'HP Drain': {'Value': 1}, 'MP Drain': {'Value': 0.5}}},
              'Kamikaze': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'Single Enemy', 'Power': 78,
                           'Correction': 20, 'Limit': 227, 'Accuracy': 100, 'Special Effects':
                               {'Kill': {'Target': 'Self'}}},
              'Sacrifice': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'Random Enemies', 'Hits': 4,
                            'Power': 56, 'Correction': 16, 'Limit': 158, 'Accuracy': 100, 'Special Effects':
                                {'Kill': {'Target': 'Self'}}},
              'Last Resort': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'All Enemies', 'Power': 59,
                              'Correction': 17, 'Limit': 167, 'Special Effects': {'Kill': {'Target': 'Self'}}},
              'Megido': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'All Enemies', 'Power': 70,
                         'Correction': 20, 'Limit': 197, 'Accuracy': 100, 'MP': 30},
              'Megidola': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'All Enemies', 'Power': 80,
                           'Correction': 23, 'Limit': 225, 'Accuracy': 100, 'MP': 37},
              'Megidolaon': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'All Enemies', 'Power': 90,
                             'Correction': 26, 'Limit': 253, 'Accuracy': 100, 'MP': 50},
              'Beast Roar': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'All Enemies', 'Power': 80,
                             'Correction': 23, 'Limit': 225, 'Accuracy': 100, 'MP': 37, 'Special Effects':
                                 {'HP Recover': {'Value': 0.1, 'Target': 'Self'}}},
              'Death Flies': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'All Enemies', 'Power': 90,
                              'Correction': 26, 'Limit': 253, 'Accuracy': 100, 'MP': 50, 'Special Effects':
                                  {'Kill': {'Element': 'Death'}}},
              'Fire of Sinai': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'Random Enemies', 'Hits': 5,
                                'Power': 90, 'Correction': 26, 'Limit': 253, 'Accuracy': 100, 'MP': 50},
              'Jiraiya Tarantella': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'All Enemies',
                                     'Power': 90, 'Correction': 26, 'Limit': 253, 'MP': 40},
              'Meditation': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'Single Enemy', 'Power': 60,
                             'Correction': 8, 'Limit': 84, 'Accuracy': 100, 'MP': 10, 'Special Effects':
                                 {'HP Drain': {'Value': 1}, 'MP Drain': {'Value': 0.5}}},
              'Pestilence': {'Category': 'Magic', 'Element': 'Almighty', 'Target': 'All Enemies', 'Power': 50,
                             'Correction': 12, 'Limit': 120, 'MP': 16, 'Special Effects':
                                 {'Kill': {'Condition': 'Target Poisoned'}}},
              'Evil Melody': {'Category': 'Magic', 'Target': 'Lowest HP', 'MP': 1, 'Special Effects':
                  {'Kill': {}}},
              'Dia': {'Category': 'Magic', 'Target': 'Single Ally', 'Power': 55, 'Correction': 16,
                      'Limit': 155, 'MP': 3, 'Special Effects': {'Heal': {}}},
              'Media': {'Category': 'Magic', 'Target': 'All Allies', 'Power': 45, 'Correction': 13,
                        'Limit': 126, 'MP': 12, 'Special Effects': {'Heal': {}}},
              'Diarama': {'Category': 'Magic', 'Target': 'Single Ally', 'Power': 75, 'Correction': 20,
                          'Limit': 220, 'MP': 7, 'Special Effects': {'Heal': {}}},
              'Mediarama': {'Category': 'Magic', 'Target': 'All Allies', 'Power': 65, 'Correction': 19,
                            'Limit': 183, 'MP': 20, 'Special Effects': {'Heal': {}}},
              'Diarahan': {'Category': 'Magic', 'Target': 'Single Ally', 'MP': 15,
                           'Special Effects': {'Heal': {}}},
              'Mediarahan': {'Category': 'Magic', 'Target': 'All Allies', 'MP': 35,
                             'Special Effects': {'Heal': {}}},
              'Prayer': {'Category': 'Magic', 'Target': 'All Allies', 'MP': 50,
                         'Special Effects': {'Heal': {}, 'Cure Ailments': {}}},
              'Mutudi': {'Category': 'Magic', 'Target': 'Single Ally', 'MP': 5,
                         'Special Effects': {'Cure Mute': {}}},
              'Patra': {'Category': 'Magic', 'Target': 'Single Ally', 'MP': 5,
                        'Special Effects': {'Cure Bind/Sleep/Panic': {}}},
              'Posumudi': {'Category': 'Magic', 'Target': 'Single Ally', 'MP': 5,
                           'Special Effects': {'Cure Poison': {}}},
              'Paraladi': {'Category': 'Magic', 'Target': 'Single Ally', 'MP': 5,
                           'Special Effects': {'Cure Stun': {}}},
              'Petradi': {'Category': 'Magic', 'Target': 'Single Ally', 'MP': 5,
                          'Special Effects': {'Cure Stone': {}}},
              'Me Patra': {'Category': 'Magic', 'Target': 'All Allies', 'MP': 12,
                           'Special Effects': {'Cure Bind/Sleep/Panic': {}}},
              'Recarm': {'Category': 'Magic', 'Target': 'Dead Ally', 'MP': 20, 'Special Effects':
                  {'Revive': {'Value': 0.5}}},
              'Samarecarm': {'Category': 'Magic', 'Target': 'Dead Ally', 'MP': 35, 'Special Effects':
                  {'Revive': {'Value': 1}}},
              'Recarmdra': {'Category': 'Magic', 'Target': 'Other Allies', 'MP': 1, 'Special Effects':
                  {'Heal': {}, 'MP Recover': {'Value': 1}, 'Kill': {'Target': 'Self'}}},
              'Holy Melody': {'Category': 'Magic', 'Target': 'Lowest HP', 'MP': 1, 'Special Effects':
                  {'Heal': {}, 'MP Recover': {'Value': 1}}},
              'Focus': {'Category': 'Magic', 'Target': 'Self', 'MP': 5, 'Special Effects':
                  {'Focus': {}}},
              'Tarukaja': {'Category': 'Magic', 'Target': 'All Allies', 'MP': 12,
                           'Special Effects': {'Tarukaja': {}}},
              'Makakaja': {'Category': 'Magic', 'Target': 'All Allies', 'MP': 12,
                           'Special Effects': {'Makakaja': {}}},
              'Rakukaja': {'Category': 'Magic', 'Target': 'All Allies', 'MP': 12,
                           'Special Effects': {'Rakukaja': {}}},
              'Sukukaja': {'Category': 'Magic', 'Target': 'All Allies', 'MP': 12,
                           'Special Effects': {'Sukukaja': {}}},
              'Tarunda': {'Category': 'Magic', 'Target': 'All Enemies', 'MP': 20,
                          'Special Effects': {'Tarunda': {}}},
              'Rakunda': {'Category': 'Magic', 'Target': 'All Enemies', 'MP': 12,
                          'Special Effects': {'Rakunda': {}}},
              'Sukunda': {'Category': 'Magic', 'Target': 'All Enemies', 'MP': 12,
                          'Special Effects': {'Sukunda': {}}},
              'Fog Breath': {'Category': 'Magic', 'Target': 'All Enemies', 'MP': 30,
                             'Special Effects': {'Fog Breath': {}}},
              'War Cry': {'Category': 'Magic', 'Target': 'All Enemies', 'MP': 40,
                          'Special Effects': {'War Cry': {}}},
              'Debilitate': {'Category': 'Magic', 'Target': 'All Enemies', 'MP': 48,
                             'Special Effects': {'Debilitate': {}}},
              'Taunt': {'Category': 'Magic', 'Target': 'All Enemies', 'MP': 20,
                        'Special Effects': {'Taunt': {}}},
              'Dekunda': {'Category': 'Magic', 'Target': 'All Allies', 'MP': 10,
                          'Special Effects': {'Dekunda': {}}},
              'Dekaja': {'Category': 'Magic', 'Target': 'All Enemies', 'MP': 10,
                         'Special Effects': {'Dekaja': {}}},
              'Makarakarn': {'Category': 'Magic', 'Target': 'All Allies', 'MP': 45, 'Special Effects':
                  {'Reflect Magic': {}}},
              'Tetrakarn': {'Category': 'Magic', 'Target': 'All Allies', 'MP': 45, 'Special Effects':
                  {'Reflect Phys': {}}},
              'Tetraja': {'Category': 'Magic', 'Target': 'All Allies', 'MP': 15, 'Special Effects':
                  {'Void Expel/Death': {}}},
              'Guardian Raptor': {'Category': 'Magic', 'Target': 'All Allies', 'MP': 10, 'Special Effects':
                  {'Dekunda': {}}},
              'Provoke': {'Category': 'Magic', 'Target': 'All Enemies', 'Special Effects':
                  {'Taunt': {}, 'MP Recover': {'Value': 0.25, 'Target': 'Self'}}},
              'Red Capote': {'Category': 'Magic', 'Target': 'Self', 'MP': 36, 'Special Effects':
                  {'Red Capote': {}}},
              'Analyze': {'Category': 'Magic', 'Target': 'Single Enemy', 'MP': 2, 'Special Effects':
                  {'Analyze': {}}},
              'Makatora': {'Category': 'Magic', 'Target': 'Single Ally', 'MP': 10, 'Special Effects':
                  {'Share MP': {'Value': 10}}},
              'Beckon Call': {'Category': 'Magic', 'Target': 'Random Stock Ally', 'MP': 20,
                              'Special Effects': {'Summon': {}}},
              'Summon': {'Category': 'Magic', 'Target': 'Stock Ally', 'Special Effects':
                  {'Summon': {}}},
              'Life Stone': {'Category': 'Item', 'Target': 'Single Ally',
                             'Special Effects': {'HP Recover': {'Value': 0.25}}},
              'Chakra Drop': {'Category': 'Item', 'Target': 'Single Ally',
                              'Special Effects': {'MP Recover': {'Value': 0.25}}}
              }


# In[9]:


sfx = []
for move, move_info in moves_dict.items():
    try:
        for effect in move_info['Special Effects']:
            sfx.append(effect)
    except KeyError:
        pass
sfx = sorted(list(set(sfx)))
#print(sfx)

sfx_values = []
for move, move_info in moves_dict.items():
    try:
        for effect, effect_info in move_info['Special Effects'].items():
            if 'Value' in effect_info:
                sfx_values.append((move, effect, effect_info['Value']))
    except KeyError:
        pass
sfx_values = sorted(list(set(sfx_values)))
#print(sfx_values)
sfx_types = []
for value in sfx_values:
    sfx_types.append(value[1])
sfx_types = list(set(sfx_types))
#print(sfx_types)


# In[10]:


# mandatory: effect
# optional: element, value
# do boosts need value? wouldn't be hard to implement, just not necessary if they're all *1.5
passives_dict = {'Anti-Phys': [{'Effect': 'Resist', 'Element': 'Phys'}],
                 'Phys Drain': [{'Effect': 'Absorb', 'Element': 'Phys'}],
                 'Phys Repel': [{'Effect': 'Reflect', 'Element': 'Phys'}],
                 'Anti-Fire': [{'Effect': 'Resist', 'Element': 'Fire'}],
                 'Void Fire': [{'Effect': 'Void', 'Element': 'Fire'}],
                 'Fire Drain': [{'Effect': 'Absorb', 'Element': 'Fire'}],
                 'Fire Repel': [{'Effect': 'Reflect', 'Element': 'Fire'}],
                 'Anti-Ice': [{'Effect': 'Resist', 'Element': 'Ice'}],
                 'Void Ice': [{'Effect': 'Void', 'Element': 'Ice'}],
                 'Ice Drain': [{'Effect': 'Absorb', 'Element': 'Ice'}],
                 'Ice Repel': [{'Effect': 'Reflect', 'Element': 'Ice'}],
                 'Anti-Elec': [{'Effect': 'Resist', 'Element': 'Elec'}],
                 'Void Elec': [{'Effect': 'Void', 'Element': 'Elec'}],
                 'Elec Drain': [{'Effect': 'Absorb', 'Element': 'Elec'}],
                 'Elec Repel': [{'Effect': 'Reflect', 'Element': 'Elec'}],
                 'Anti-Force': [{'Effect': 'Resist', 'Element': 'Force'}],
                 'Void Force': [{'Effect': 'Void', 'Element': 'Force'}],
                 'Force Drain': [{'Effect': 'Absorb', 'Element': 'Force'}],
                 'Force Repel': [{'Effect': 'Reflect', 'Element': 'Force'}],
                 'Anti-Expel': [{'Effect': 'Resist', 'Element': 'Expel'}],
                 'Void Expel': [{'Effect': 'Void', 'Element': 'Expel'}],
                 'Anti-Death': [{'Effect': 'Resist', 'Element': 'Death'}],
                 'Void Death': [{'Effect': 'Void', 'Element': 'Death'}],
                 'Anti-Curse': [{'Effect': 'Resist', 'Element': 'Curse'}],
                 'Void Curse': [{'Effect': 'Void', 'Element': 'Curse'}],
                 'Anti-Nerve': [{'Effect': 'Resist', 'Element': 'Nerve'}],
                 'Void Nerve': [{'Effect': 'Void', 'Element': 'Nerve'}],
                 'Anti-Mind': [{'Effect': 'Resist', 'Element': 'Mind'}],
                 'Void Mind': [{'Effect': 'Void', 'Element': 'Mind'}],
                 'Fire Boost': [{'Effect': 'Boost', 'Element': 'Fire'}],
                 'Ice Boost': [{'Effect': 'Boost', 'Element': 'Ice'}],
                 'Elec Boost': [{'Effect': 'Boost', 'Element': 'Elec'}],
                 'Force Boost': [{'Effect': 'Boost', 'Element': 'Force'}],
                 'Life Bonus': [{'Effect': 'HP Bonus', 'Value': 1.1}],
                 'Life Gain': [{'Effect': 'HP Bonus', 'Value': 1.2}],
                 'Life Surge': [{'Effect': 'HP Bonus', 'Value': 1.3}],
                 'Mana Bonus': [{'Effect': 'MP Bonus', 'Value': 1.1}],
                 'Mana Gain': [{'Effect': 'MP Bonus', 'Value': 1.2}],
                 'Mana Surge': [{'Effect': 'MP Bonus', 'Value': 1.3}],
                 'Counter': [{'Effect': 'Counter', 'Value': 1}],
                 'Retaliate': [{'Effect': 'Counter', 'Value': 1.5}],
                 'Avenge': [{'Effect': 'Counter', 'Value': 2}],
                 'Drain Attack': [{'Effect': 'Drain', 'Value': 0.25}, {'Effect': 'Crit', 'Value': 0.33}],
                 'Might': [{'Effect': 'Crit', 'Value': 3}],
                 'Dark Might': [{'Effect': 'Dark Might'}],
                 'Bright Might': [{'Effect': 'Bright Might'}],
                 'Attack All': [{'Effect': 'Attack All'}],
                 'Endure': [{'Effect': 'Endure'}],
                 'Pierce': [{'Effect': 'Pierce'}],
                 'Raidou the Aeon': [{'Effect': 'Boost'}, {'Effect': 'Pierce'}]}


# In[11]:


# sorted by priority
status_list = ['Stone', 'Fly', 'Stun', 'Charm', 'Poison', 'Mute', 'Bind', 'Panic', 'Sleep', 'Freeze', 'Shock']


# In[12]:


unimplemented_moves = []
for demon in demon_dict:
    base_moves = except_key(demon_dict, demon, 'Base Moves', [])
    for move in base_moves:
        if move not in moves_dict and move not in passives_dict:
            unimplemented_moves.append(move)
    learned_moves = except_key(demon_dict, demon, 'Learned Moves', [])
    for move in learned_moves:
        if move[0] not in moves_dict and move[0] not in passives_dict:
            unimplemented_moves.append(move[0])
for magatama in magatama_dict:
    moves = except_key(magatama_dict, magatama, 'Moves', [])
    for move in moves:
        if move[0] not in moves_dict and move[0] not in passives_dict:
            unimplemented_moves.append(move[0])
if 'Pierce' not in passives_dict:
    unimplemented_moves.append('Pierce')
unimplemented_moves = sorted(list(set(unimplemented_moves)))

RANDOM_DEMON_RANGE = 12

# In[13]:


#program-specific global functions

def find_evolve_count(demon):
    searching_evolutions = True
    evolve = 0
    while searching_evolutions:
        temp_evolve = evolve
        for demon_name in demon_dict:
            if demon == except_key(demon_dict, demon_name, 'Evolution', 'None')[0]:
                demon = demon_name
                evolve += 1
        if temp_evolve == evolve:
            searching_evolutions = False
    return demon, evolve


def game_help(topic='None'):
    viewing = True
    while viewing:
        if topic == 'None':
            main_topics = ['Intro', 'Game Modes', 'Player Select', 'Difficulty', 'Choosing a Party', 'Move Selection']
            main_topics += ['Target Selection', 'Game End']
            program_topics = ['Random Party Selection', 'View Commands', 'Demi-Fiend Creation']
            mechanic_topics = ['Battle Basics', 'Press Turns', 'Resistances', 'Special Effects', 'The Stock']
            mechanic_topics += ['Demi-Fiend', 'Kagutsuchi']
            experiment_topics = ['Settings Overview', 'Set Trials', 'Set Game Mode', 'Set Same Teams']
            experiment_topics += ['Set Target Level', 'Set Demons', 'Set Kagutsuchi', 'Set Log Games', 'Set File Name']
            experiment_topics += ['Default Settings']
            topics = main_topics + program_topics + mechanic_topics + experiment_topics
            if 'back' in topics:
                topics.remove('back')
            help_explain_str = 'For a detailed look at any of the topics below, type "help {topic}". '
            help_explain_str += 'Type "back" to return to the game.\n\n'
            help_explain_str += 'Topics:\n'
            help_explain_str += f'Instructions: {print_list(main_topics)}\n'
            help_explain_str += f'Game Mechanics: {print_list(mechanic_topics)}\n'
            help_explain_str += f'Program-Specific Info: {print_list(program_topics)}\n'
            help_explain_str += f'Settings for Experiment Mode: {print_list(experiment_topics)}'
            print(help_explain_str)
            topics.append('back')
            topic = input('What would you like to view? ')
            if topic == '':
                topic = 'back'
            else:
                topic = process.extractOne(topic, topics)[0]
            print()
        if topic == 'back':
            break
        if topic == 'Intro':
            output = 'Nocturne Showdown is a text-based recreation of the combat found in '
            output += "Atlus's Shin Megami Tensei: Nocturne. "
            output += 'The game is known for the "Press Turn" system, which rewards '
            output += 'exploiting enemy weaknesses and landing critical hits with extra turns.'
        elif topic == 'Game Modes':
            output = 'Currently, two game modes exist: "4 vs. 4" and "Experiment". '
            output += 'You can access either one by typing out its name in the input prompt.\n\n'
            output += '4 vs. 4 is the standard mode, and can be accessed through the selection prompt '
            output += 'by entering nothing, as well as typing out "4 vs. 4". '
            output += 'The name refers to the number of party members on each team, not the number of players '
            output += 'required. This mode uses 2 controllers, which can be any combination of '
            output += 'human players and computers (more info in the "player selection" section).\n\n'
            output += 'Experiment is mainly used for simulating games with the computer. '
            output += 'You can modify the settings (see "Experiment Settings"), but note that you will not be able to '
            output += 'actually participate in gameplay.'
        elif topic == 'Player Select':
            output = 'You can choose between "Player vs. Player", "Player vs. Comp", and "Comp vs. Comp" '
            output += 'by typing their names into the input prompt.\n\n'
            output += 'Player vs. Comp is the default option, and can be accessed by entering nothing '
            output += 'in addition to its name. This mode allows you to fight against an AI opponent.\n\n'
            output += 'Player vs. Player allows two humans to fight against each other.\n\n'
            output += 'Comp vs. Comp automatically runs a battle between two AI controllers.'
        elif topic == 'Difficulty':
            output = 'You can set the challenge level of the AI by changing the difficulty.\n\n'
            output += 'Currently, there is only one difficulty mode implemented (Easy), so '
            output += 'you will not be prompted to select a difficulty on normal start-up.'
        elif topic == 'Choosing a Party':
            output = 'Each player has the opportunity to choose some or all of their party members. '
            output += 'To do so, type the name of the demon you want into the input prompt. '
            output += 'Note that the maximum party size is four.\n\n'
            output += 'For new players, selecting a random party is likely the best option. '
            output += 'To do so, either enter nothing into the first input or type "random".\n\n'
            output += 'If you would like to select a few demons and randomize the rest, '
            output += 'enter "random" once you have chosen the demons you want. You can also type a number between '
            output += '1 and 99 (inclusive) to specify a target level for the random demons.\n\n'
            output += 'To start a battle with less than four demons, you will have to manually select your '
            output += 'party members. Once you are done, enter nothing to finish the process.\n\n'
            output += 'For more information on the random selection process, '
            output += 'see the topic titled "Random Party Selection".'
        elif topic == 'Move Selection':
            output = "On each turn, you can select an action from your demon's move list by typing its name "
            output += 'into the input prompt.\n\n'
            output += 'You can also type "view" to quickly view all demons'
            output += "' HP. There are other commands associated with the word "
            output += '"view", which you can find in the topic titled "View Commands".\n\n'
            output += 'You can also type "stop" to end the program.'
        elif topic == 'Target Selection':
            output = 'After you select a move, you will be given an opportunity to select targets and '
            output += 'confirm move execution.\n\n'
            output += 'For moves that target a single enemy or ally, you will be prompted to select a number. '
            output += 'A list of possible targets, along with their particular numbers, '
            output += 'is printed above the prompt.\n\n'
            output += "For moves that don't require target specification, such as those that target all enemies, "
            output += 'you can simply enter nothing in the prompt to continue.\n\n'
            output += 'In either case, you may type "back" to return to move selection if you '
            output += 'want to change your action.'
        elif topic == 'Game End':
            output = 'After finishing a game, you will be given the option to play again (type "y" or "yes" for yes or '
            output += 'anything else for no). Saying "no" will end the program.\n\n'
            output += 'If you choose to play again, you can choose to play with the same teams (again, "y" or "yes" '
            output += 'for yes or anything else for no). Selecting "yes" will restart the current game with the same '
            output += 'settings and parties, while selecting "no" sends you to the start of the program and allows you '
            output += 'to reselect settings.'
        elif topic == 'Random Party Selection':
            output = 'A random party will consist of 3 demons and 1 demi-fiend (a unique type of demon).\n\n'
            output += f'Demons are chosen to be within {RANDOM_DEMON_RANGE} levels of the party average.'
            output += 'If there is no existing average (because the demon would be the first in the party), '
            output += 'the demon is simply selected randomly.\n\n'
            output += 'If the other party has been decided, the first demon of the new party will be chosen '
            output += 'based on the average of the other party.'
        elif topic == 'View Commands':
            output = 'view: Provides a quick view of the demons on the battlefield and their HP.\n\n'
            output += 'view demon_name: Searches the battlefield for any demons with name demon_name '
            output += 'and displays their more detailed information.\n'
            output += 'view number: Displays detailed information on the demon associated with that number. '
            output += "A demon's number is listed next to their name in the quick view.\n"
            output += 'view self: Shortcut for showing information of the current demon.\n\n'
            output += 'view move_name: Displays detailed information of the move with name move_name.\n\n'
            output += 'Note that you may not receive the detailed information of demons not in your party '
            output += 'or moves that no one in your party has.'
        elif topic == 'Demi-Fiend Creation':
            output = 'Each magatama defines four things: level, stats, moves, and resistances.\n\n'
            output += 'Level: Each magatama contains many moves, which are normally learned through leveling up. '
            output += "A Demi-Fiend's level is equal to the highest-level move in a magatama.\n\n"
            output += 'The one exception is the Masakados magatama, whose moves can all be learned at any level. '
            output += 'As this is the strongest magatama in the game, its level has arbitrarily been set to 95.\n\n'
            output += "Stats: The Demi-Fiend has 2 of every stat at level 1, and gains 1 stat point per level up. "
            output += 'Each magatama also provides small stat bonuses. '
            output += "In the original game, you could freely allocate the Demi-Fiend's stats each level. "
            output += 'Instead, stats are assigned randomly, but with higher weight towards the inherent bonuses '
            output += 'of the selected magatama.\n\n'
            output += 'Moves: The Demi-Fiend gains all moves of the selected magatama. If he has less than 8 moves, '
            output += 'lower-level moves from other magatama will be added until he has 8. (The 8-move limit does not '
            output += 'include "Attack", "Summon", or "Pass".)\n\n'
            output += 'The skill "Pierce" is normally tied to the Marogareh magatama, but does not have a level '
            output += '(it is unlocked through story events). Pierce can be obtained randomly by any magatama, but is '
            output += 'not guaranteed if Marogareh is selected.\n\n'
            output += 'Resistances: The Demi-Fiend has the inherent resistances and weaknesses of the chosen magatama, '
            output += 'as well as those obtained through passive abilities. Note that it is possible for resistances '
            output += 'gained through passives to override inherent weaknesses.'
        elif topic == 'Battle Basics':
            output = 'The goal of the game is to reduce all of your opponent'
            output += "'s demons' HP to zero.\n\n"
            output += 'Turns will alternate between you and your opponent. On each turn, you will be '
            output += 'able to act once for each demon in your party. However, this number can increase '
            output += 'or decrease based on the results of your actions (see the "Press Turns" topic).\n\n'
        elif topic == 'Press Turns':
            output = 'When it becomes your turn, you start with a number of "press turn" icons '
            output += 'equal to the number of demons in your party. '
            output += 'These are indicated by the symbol [X]. '
            output += 'Demons in your party act in order of their agility. '
            output += 'Normally, each action consumes one press turn. '
            output += 'However, some actions will convert full icons to half icons instead, denoted by [*]. '
            output += 'This gives you extra actions, although '
            output += 'no more than four half-icons can be gained in a turn. '
            output += 'Other actions might consume more than one icon. '
            output += 'Once you have used all of your '
            output += 'press turns, your turn ends and your opponent starts their turn.\n\n'
            output += 'Exceptions to the one-action-per-icon rule are as follows:\n'
            output += 'If an enemy repels or absorbs your attack, you lose all of your press turns.\n'
            output += 'If an enemy voids your attack, you lose two icons.\n'
            output += "If you hit an enemy's weakness or land a critical hit, one full turn icon will "
            output += 'change to a half icon. (If there are no full icons left, one half icon will be used.)\n'
            output += 'If you pass the turn, one half icon will be consumed. '
            output += 'If there are no half icons, one full icon will change to a half icon.\n'
        elif topic == 'Resistances':
            output = 'The following resistances are listed in order of priority. For example, if a demon both '
            output += 'absorbs and is weak to an attack, the attack will be absorbed. This is possible through '
            output += 'resistance-granting passives.\n\n'
            output += 'Reflect: Sends the damage of a move back at the controller.\n'
            output += 'Absorb: Heals for the amount of damage dealt instead of taking damage.\n'
            output += 'Void: Takes no damage.\n'
            output += 'Weak: Takes 1.5x damage.\n'
            output += 'Resist: Takes 0.5x damage.\n'
            output += 'If a demon is weak to an attack but also resists it, the damage dealt is 0.75x and the '
            output += 'attacker gets an extra press turn.'
        elif topic == 'Special Effects':
            output = 'Some moves have additional special effects, such as HP draining or a chance to inflict ailments. '
            output += 'These will only trigger if the move connects.\n\n'
            output += 'The chance of an effect occuring is affected by the resistances of a demon.'
            output += "If a demon voids an effect's element or better, it will not trigger. "
            output += 'If the demon is weak to it, the effect has a 1.5x chance of occuring, and so on. '
            output += '(See the "Resistances" topic for exact percentages). Note that the elements of special effects '
            output += "do not always align with their parent move's element.\n\n"
            output += 'If an effect has a less-than-100% chance of triggering and it does not trigger, no '
            output += 'press turn penalty is incurred. However, most moves that inflict ailments can still be '
            output += 'dodged. The phrase "dodged the attack" means that the attack itself missed, while '
            output += '"the effect missed" means that the special effect did not trigger. (See "Press Turns" '
            output += 'for more info on the penalties.)\n\n'
            output += 'Also remember that support moves (such as healing and debuffs) do not have an element and '
            output += 'do not check for accuracy, so they will always work.'
        elif topic == 'The Stock':
            output = 'When a demon dies, instead of disappearing forever, it is sent to the stock. '
            output += 'Certain moves can interact with the stock, such as those that revive or summon demons.\n\n'
            output += 'Moves that revive demons, such as Recarm, grant HP to dead demons. However, they are still '
            output += 'located in the stock, and are unusable.\n\n'
            output += 'To bring them back to battle, you must summon them with Summon or Beckon Call. Every '
            output += 'Demi-Fiend has the move Summon, so if you can revive a dead demon, you can bring them back.\n\n'
            output += 'However, this does mean that resummoning dead demons takes two actions. In addition, if '
            output += 'the Demi-Fiend dies, you lose access to Summon, making it harder to bring dead demons back.'
        elif topic == 'Demi-Fiend':
            output = 'The Demi-Fiend is the main character of Shin Megami Tensei: Nocturne, and as such is always '
            output += 'in the party.\n\n'
            output += 'In the original game, his moves and resistances come from special items called "magatama". '
            output += 'In this game, his magatama is chosen randomly (just like random demons). He gains his level, '
            output += 'stats, resistances, and moves from that magatama. See "Demi-Fiend Creation" for more info.\n\n'
            output += 'During party selection, you can get a demi-fiend with a random magatama by typing "demi-fiend". '
            output += 'To choose a specific magatama, you can type the name of the magatama instead.\n\n'
            output += 'During battles in the original game, if the Demi-Fiend died, it would result in a game over. '
            output += 'This is not the case in this game— you must defeat all opposing demons to win.'
        elif topic == 'Kagutsuchi':
            output = 'Kagutsuchi is analogous to a moon. Its phase is randomly generated at first, and then it cycles '
            output += 'through phases as more games are played.\n\n'
            output += 'The Kagutsuchi phase affects the "Bright Might" and "Dark Might" skills. Demons with '
            output += 'Bright Might will always crit with their normal attack on full Kagutsuchi. The same is true '
            output += 'for Dark Might on new Kagutsuchi. Otherwise, Kagutsuchi carries very little gameplay '
            output += 'significance.'
        elif topic == 'Settings Overview':
            output = 'There are a variety of changeable settings in Experiment Mode. To select one, type its name '
            output += 'into the prompt. Enter nothing to end setting selection and begin game simulation.\n\n'
            output += 'For info on each specific setting, refer to the other topics listed in "Settings for '
            output += 'Experiment Mode". Also see "Default Settings" for info on returning settings to their default '
            output += 'values.'
        elif topic == 'Set Trials':
            output = 'The number of trials is the number of games to be simulated. When changing the value, type '
            output += 'a number greater than or equal to 1.'
        elif topic == 'Set Game Mode':
            output = 'The game mode is the type of game to be played (see "Game Modes" for more info). '
            output += 'Currently, there is only one option (4 vs. 4), so that will be selected by default.'
        elif topic == 'Set Same Teams':
            output = 'This determines whether teams should stay the same or be re-made after every game. If you would '
            output += 'like to maintain the same teams each game, enter "y" or "yes" into the prompt. Otherwise, '
            output += 'type "n" or "no". Note that remaking teams will increase experiment time for large trial counts.'
        elif topic == 'Set Target Level':
            output = 'This determines the average level of either party 1 or 2. To change '
            output += 'this parameter, enter a number between 1 and 99. You can also type "none" to avoid '
            output += 'specifying.'
        elif topic == 'Set Demons':
            output = 'Allows you to specify demons for each party. See the topic "Choosing a Party" '
            output += 'for info on how input works. The main difference is that you can break demon selection by '
            output += 'entering nothing before you have selected a full party of 4. Doing so will allow the remaining '
            output += 'spots to be randomly chosen. Also, the word "random" has no special effect.'
        elif topic == 'Set Kagutsuchi':
            output = 'This allows you to specify a kagutsuchi phase, and involves two prompts.\n\nFor the '
            output += 'first, type a number between 0 and 8 to represent the phase, where 0 is new and 8 is full. '
            output += 'You can also specify "dead", which means Kagutsuchi will never have an effect, or "random", '
            output += 'which gives a random phase.\n\n'
            output += 'The second prompt allows you to disable phase rotation between games. To do so, type "y" or '
            output += '"yes". Otherwise, type "n" or "no".\n\n'
        elif topic == 'Set Log Games':
            output = 'Choose if a record of the games played should be saved to a text file. '
            output += 'If you would like to, type "y" or "yes". Otherwise, type "n" or "no". Nte that '
            output += 'saving a log prevents games from being displayed in the console, whereas disabling logging '
            output += 'means that all games will print to the console.\n\n'
        elif topic == 'Set File Name':
            output = 'Allows you to choose a custom file name for the game log. The inputted name must only '
            output += 'contain letters and numbers. This setting only matters if game logging is enabled.'
        elif topic == 'Default Settings':
            output = 'In general, entering nothing in the prompt for a setting will '
            output += 'reset it to its default value.\n\n When choosing a setting, you can also type "default" '
            output += 'to restore all settings to their default values (after a confirmation prompt).'
        print(output+'\n')
        topic = 'None'

def h_input(message, topic='None'):
    user_input = input(message)
    while user_input == 'help':
        print()
        game_help(topic=topic)
        user_input = input(message)
    return user_input

#classes

class Kagutsuchi:
    # can implement other numeric/comparison functions if needed
    def __init__(self, phase='Random', frozen=False):
        if phase == 'Dead':
            self.dead = True
            self.phase = random.randint(0, 8)
        elif phase == 'Random':
            self.dead = False
            self.phase = random.randint(0, 8)
        else:
            if not type(phase) == int:
                raise ValueError('argument must be an int (or the strings "Dead" or "Random")')
            if phase > 8 or phase < 0:
                raise ValueError('argument must be between 0 and 8')
            self.dead = False
            self.phase = phase
        if self.phase == 0:
            self.direction = "increasing"
        elif self.phase == 8:
            self.direction = "decreasing"
        else:
            self.direction = random.choice(["increasing", "decreasing"])
        self.frozen = frozen

    def __add__(self, n):
        if not self.frozen:
            while n > 0:
                if self.direction == "increasing":
                    self.phase += 1
                elif self.direction == "decreasing":
                    self.phase -= 1
                if self.phase == 8:
                    self.direction = "decreasing"
                elif self.phase == 0:
                    self.direction = "increasing"
                n -= 1
        return self

    def __eq__(self, n):
        if self.phase == n and not self.dead:
            return True
        return False

    def more_info(self):
        return f'Phase: {str(self)}, {self.direction}{" (FROZEN)" if self.frozen else ""}'

    def __str__(self):
        if self.dead:
            return 'Dead'
        if self.phase == 0:
            return 'New'
        elif self.phase == 4:
            return 'Half'
        elif self.phase == 8:
            return 'Full'
        else:
            return f'{self.phase}/8'


# In[14]:


class Move:
    def __init__(self, name):
        self.name = name
        self.target = moves_dict[name]['Target']
        self.category = moves_dict[name]['Category']
        self.dmg_calc = except_key(moves_dict, name, 'Damage Calc', 'None')
        if self.dmg_calc == 'None' and self.category == 'Magic':
            self.dmg_calc = 'Mag'
        self.element = except_key(moves_dict, name, 'Element', 'None')
        self.hits = except_key(moves_dict, name, 'Hits', 1)
        self.power = except_key(moves_dict, name, 'Power', 'None')
        self.correction = except_key(moves_dict, name, 'Correction', 'None')
        self.limit = except_key(moves_dict, name, 'Limit', 'None')
        if self.power != 'None' and self.correction != 'None' and self.limit != 'None':
            self.peak = round(((self.limit - self.correction) / self.power) * (255 / 24))
        else:
            self.peak = 'None'
        self.accuracy = except_key(moves_dict, name, 'Accuracy', 'None')
        self.mp = except_key(moves_dict, name, 'MP', 0)
        self.hp = except_key(moves_dict, name, 'HP', 0)
        self.specials = except_key(moves_dict, name, 'Special Effects', {})
        if self.element == 'Phys':
            self.specials['Shatter'] = {'Accuracy': 50}
        elif self.element == 'Force':
            self.specials['Shatter'] = {'Accuracy': 75}
        for effect_info in self.specials.values():
            self.special_default(effect_info)
        self.crit = except_key(moves_dict, name, 'Crit', 'None')
        self.pierce = False
        self.reset()

    def reset(self):
        self.reflected = False
        self.temp_dmg_factor = 1

    def special_default(self, effect_info):
        '''Takes in effect_info dict; updates it to defaults. Separate from __init__ method
           for use in adding new special effects to moves (via passives; ex. bright/dark might)'''
        if 'Element' not in effect_info:
            effect_info['Element'] = self.element
        if 'Accuracy' not in effect_info:
            effect_info['Accuracy'] = 100
        if 'Value' not in effect_info:
            effect_info['Value'] = 0
        if 'Target' not in effect_info:
            effect_info['Target'] = 'Same'
        if 'Condition' not in effect_info:
            effect_info['Condition'] = 'None'

    def hp_cost(self, user):
        return int(self.hp * user.max_hp / 100)

    def user_cost_string(self, user):
        if self.mp != 0:
            return f'{self.mp} MP'
        elif self.hp != 0:
            return f'{self.hp_cost(user)} HP'
        else:
            return 'None'

    def calculate_element_effect(self, target):
        '''more extensive than Demon.find_element_effect; considers barriers and frozen status. Non-destructive;
        returns a tuple with info on barriers hit.'''
        barrier_effect = 'None'
        barrier = 'None'
        element_effect = target.find_element_effect(self.element)
        if self.reflected:
            if element_effect == 'Reflect' or element_effect == 'Absorb':
                element_effect = 'Void'
        # check for temp barriers
        barrier_effect = 'None'
        if self.element != 'Almighty' and self.element != 'None':
            if target.tetrakarn and self.category == 'Physical' and 'Freeze' not in target.list_statuses():
                barrier_effect = 'Reflect'
                barrier = 'Tetrakarn'
            elif target.makarakarn and self.category == 'Magic':
                barrier_effect = 'Reflect'
                barrier = 'Makarakarn'
            elif target.tetraja:
                if self.element == 'Expel' or self.element == 'Death':
                    barrier_effect = 'Void'
                    barrier = 'Tetraja'
        if self.reflected and barrier_effect == 'Reflect':
            barrier_effect = 'Void'
        # redo weaknesses if target is frozen
        if self.category == 'Physical' and 'Freeze' in target.list_statuses():
            if element_effect in ['Reflect', 'Absorb', 'Void', 'Resist']:
                element_effect = 'None'
            elif element_effect == 'Weak/Resist':
                element_effect = 'Weak'
        return (element_effect, barrier_effect, barrier)


    def calculate_accuracy(self, user, target):
        if 'Shock' in target.list_statuses() or 'Freeze' in target.list_statuses():
            hit_chance = 100
        elif self.accuracy == 'None':
            hit_chance = 100
        elif self.category == 'Magic':
            hit_chance = self.accuracy * (user.level + 2 * user.mag + user.luck / 2 + 17.5)
            hit_chance /= target.level + 1.5 * target.ag + target.luck + 17.5
            hit_chance *= user.suku_mod() / target.suku_mod()
        elif self.category == 'Physical':
            hit_chance = self.accuracy + user.ag * 6.25 / ((user.level / 5) + 3)
            hit_chance -= target.ag * 6.25 / ((target.level / 5) + 3)
            hit_chance *= user.suku_mod() / target.suku_mod()
            if 'Stun' in user.list_statuses() and self.category == 'Physical':
                hit_chance *= 1 / 4
        else:
            hit_chance = 100
        return hit_chance

    def calculate_base_damage(self, user, target, power_factor=1):
        # power factor used for mana drains
        if self.power != 'None':
            power = self.power * power_factor
            if self.dmg_calc == 'Mag':
                if user.level <= self.peak:
                    damage = 0.004 * (5 * (user.mag + 36) - user.level)
                    damage *= ((24 * power * user.level / 255) + self.correction)
                elif user.level < 160:
                    damage = 0.004 * (5 * (user.mag + 36) - user.level) * self.limit
                else:
                    damage = 0.02 * (user.mag + 4) * self.limit
            elif self.dmg_calc == 'Level':
                damage = (user.level + user.str) * power / 15
            elif self.dmg_calc == 'HP':
                damage = user.max_hp * power * 0.0114
            else:
                damage = 'None'
        elif 'Heal' in self.specials:
            damage = target.max_hp - target.hp
        else:
            damage = 'None'
        if damage != 'None':
            if self.category == 'Physical':
                damage *= user.taru_mod()
            elif self.category == 'Magic':
                damage *= user.maka_mod()
            if 'Heal' not in self.specials:
                damage /= target.raku_mod()
        if 'Stone' in target.list_statuses():
            if self.element == 'Fire' or self.element == 'Ice' or self.element == 'Elec':
                damage *= 0.1
        return damage

    def calculate_crit(self, user, target, kagutsuchi=Kagutsuchi('Dead')):
        crit_proc = False
        if self.crit != 'None':
            if 'Shock' in target.list_statuses() or 'Freeze' in target.list_statuses():
                crit_chance = 100
            elif 'Bright Might' in self.specials and kagutsuchi == 8:
                crit_chance = 100
            elif 'Dark Might' in self.specials and kagutsuchi == 0:
                crit_chance = 100
            else:
                if self.accuracy == 'None':
                    base_accuracy = 100
                else:
                    base_accuracy = self.accuracy
                crit_chance = self.crit * self.calculate_accuracy(user, target) / base_accuracy
            if crit_chance >= random.randint(1, 100):
                crit_proc = True
        return crit_proc

    def unknown_str(self):
        output = f'Move: {self.name}\n'
        output += 'Cost: ???\n'
        output += 'Type: ???\n'
        output += 'Element: ???\n'
        output += 'Target: ???\n'
        output += 'Base Power: ???\n'
        output += 'Base Accuracy: ???\n'
        output += 'Base Crit Chance: ???\n'
        output += 'Special Effects: ???\n\n'
        output += 'Analyze a demon with this move for more information...\n'
        return output

    def __str__(self):
        output = f'Move: {self.name}\n'
        if self.mp != 0:
            output += f'Cost: {self.mp} MP\n'
        elif self.hp != 0:
            output += f'Cost: {self.hp}% HP\n'
        else:
            output += f'Cost: None\n'
        if self.dmg_calc == 'HP' or self.dmg_calc == 'Level':
            output += f'Type: {self.category} ({self.dmg_calc}-based)\n'
        else:
            output += f'Type: {self.category}\n'
        output += f'Element: {self.element}\n'
        output += f'Target: {self.target}\n'
        if self.hits != 1:
            if 'Random' in self.target:
                output += 'Max '
            output += f'Hits: {self.hits}\n'
        if self.power != 'None':
            output += f'Base Power: {self.power}\n'
        if self.accuracy != 'None':
            output += f'Base Accuracy: {self.accuracy}\n'
        if self.crit != 'None':
            output += f'Base Crit Chance: {self.crit}\n'
        for effect, effect_info in self.specials.items():
            effect_element = effect_info['Element']
            output += f'Special Effect: {effect} ('
            if effect_info['Value'] != 0:
                if effect_info['Value'] <= 1:
                    output += f'{effect_info["Value"] * 100}'
                else:
                    output += f'{effect_info["Value"]}'
                if 'Recover' in effect or effect == 'Reduce HP':
                    output += '% of max'
                elif 'Drain' in effect:
                    output += '% of damage dealt'
                elif effect == 'Share MP':
                    output += 'MP'
                elif effect == 'Revive':
                    output += '% of max HP'
                output += ', '
            if effect_info['Condition'] != 'None':
                output += f'Condition: {effect_info["Condition"]}, '
            if effect_info['Target'] != 'Same':
                output += f'Target: {effect_info["Target"]}, '
            if effect_info['Element'] != self.element:
                output += f'Element: {effect_info["Element"]}, '
            output += f'{effect_info["Accuracy"]}% chance)\n'
        return output


# In[15]:


class PassiveAbility:
    def __init__(self, info):
        self.effect = info['Effect']
        try:
            self.element = info['Element']
        except KeyError:
            self.element = 'None'
        try:
            self.value = info['Value']
        except KeyError:
            self.value = 'None'

    def init_apply(self, demon):
        if self.effect == 'Reflect':
            demon.reflect.add(self.element)
        elif self.effect == 'Absorb':
            demon.absorb.add(self.element)
        elif self.effect == 'Void':
            demon.void.add(self.element)
        elif self.effect == 'Resist':
            demon.resist.add(self.element)
        elif self.effect == 'HP Bonus':
            demon.hp = int(demon.hp * self.value)
            demon.max_hp = int(demon.max_hp * self.value)
        elif self.effect == 'MP Bonus':
            demon.mp = int(demon.mp * self.value)
            demon.max_mp = int(demon.max_mp * self.value)
        elif self.effect == 'Endure':
            demon.endure = True
        elif self.effect == 'Crit':
            if demon.get_move('Attack').crit != 'None':
                demon.get_move('Attack').crit *= self.value
        elif self.effect == 'Bright Might':
            demon.get_move('Attack').specials['Bright Might'] = {}
            demon.get_move('Attack').special_default(demon.get_move('Attack').specials['Bright Might'])
        elif self.effect == 'Dark Might':
            demon.get_move('Attack').specials['Dark Might'] = {}
            demon.get_move('Attack').special_default(demon.get_move('Attack').specials['Dark Might'])
        elif self.effect == 'Drain':
            demon.get_move('Attack').specials['HP Drain'] = {'Value': self.value}
            demon.get_move('Attack').special_default(demon.get_move('Attack').specials['HP Drain'])
        elif self.effect == 'Attack All':
            demon.get_move('Attack').target = 'All Enemies'
        elif self.effect == 'Pierce':
            for move in demon.moves:
                if move.category == 'Physical':
                    move.pierce = True

    def attack_apply(self, move):
        if self.effect == 'Boost':
            if self.element == move.element and self.element != 'None':
                move.temp_dmg_factor *= 1.5
            elif self.element == 'None' and move.element != 'None':
                move.temp_dmg_factor *= 1.5

    def counter_apply(self, user, target, kagutsuchi):
        if self.effect == 'Counter':
            print(f'\n{user.name} countered!')
            user.get_move('Attack').temp_dmg_factor *= self.value
            user.get_move('Attack').reflected = True
            for i in range(user.get_move('Attack').hits):
                print()
                user.use_move(user.get_move('Attack'), target, kagutsuchi)
            return True
        return False

    def __str__(self):
        output = 'Missing passive effect'
        if self.effect in ['Reflect', 'Absorb', 'Void', 'Resist']:
            resist_element = self.element
            if resist_element == 'Elec':
                resist_element = 'electric'
            output = f'{self.effect}s {resist_element} damage'
            if self.effect == 'Resist':
                output += ' by 0.5x'
        elif 'Bonus' in self.effect:
            output = f'Raises max {self.effect[0:2]} by {round((self.value - 1), 2) * 100}%'
        elif self.effect == 'Counter':
            output = f'Counters physical attacks, {self.value}x damage'
        elif self.effect == 'Boost':
            boost_element = self.element
            if boost_element == 'None':
                boost_element = 'All'
            if boost_element == 'Elec':
                boost_element = 'electric'
            output = f'Boosts {boost_element.lower()} damage by 1.5x'
        elif self.effect == 'Endure':
            output = 'Survives one fatal blow per battle with 1HP remaining'
        elif self.effect == 'Drain':
            output = f'Normal attack drains {self.value}% of damage dealt'
        elif self.effect == 'Crit':
            output = f'Changes critical rate of normal attack by {self.value}x'
        elif self.effect == 'Bright Might':
            output = 'Normal attacks always crit during full Kagutsuchi'
        elif self.effect == 'Dark Might':
            output = 'Normal attacks always crit during new Kagutsuchi'
        elif self.effect == 'Attack All':
            output = 'Normal attack targets all enemies'
        elif self.effect == 'Pierce':
            output = 'Physical moves ignore all resistances except Reflect'
        return output


# In[16]:


class Passive:
    def __init__(self, name):
        self.name = name
        self.abilities = []
        for ability in passives_dict[name]:
            self.abilities.append(PassiveAbility(ability))

    def init_apply(self, demon):
        for ability in self.abilities:
            ability.init_apply(demon)

    def attack_apply(self, move):
        for ability in self.abilities:
            ability.attack_apply(move)

    def counter_apply(self, user, target, kagutsuchi):
        for ability in self.abilities:
            if ability.counter_apply(user, target, kagutsuchi):
                break

    def unknown_str(self):
        return f'Passive: {self.name}\nEffect: ???'

    def __str__(self):
        output = f'Passive: {self.name}\nEffect'
        ability_strings = []
        for ability in self.abilities:
            ability_strings.append(str(ability))
        if len(ability_strings) >= 2:
            output += 's'
        output += f': {print_list(ability_strings)}'
        return output


# In[17]:


class Status:
    def __init__(self, name):
        self.name = name
        self.timer = 0
        if self.name == 'Freeze' or self.name == 'Shock':
            self.max_time = 1
        elif self.name == 'Charm' or self.name == 'Bind' or self.name == 'Panic' or self.name == 'Sleep':
            self.max_time = 4
        else:
            self.max_time = 'End'

    def tick(self, demon):
        self.timer += 1
        if self.max_time != 'End':
            if self.timer >= self.max_time:
                return True
            else:
                # formula is here: https://w.atwiki.jp/noctan/pages/82.html
                # i don't think there's actually a turn cap for statuses, but i put it in cuz idk
                cure_chance = demon.luck / ((20 + demon.level) / 5)
                if self.name == 'Charm':
                    cure_chance *= 40
                elif self.name == 'Sleep':
                    cure_chance *= 20
                else:
                    cure_chance *= 30
                random_remove = random.randint(1, 100)
                if random_remove <= cure_chance:
                    return True
        return False


# In[18]:


class Demon:
    def __init__(self, name='None', evolutions=0, target_lv='None', party='None'):
        self.moves = [Move('Attack')]
        self.passives = []
        self.has_endure = False
        self.analyzed = False
        self.party = party
        self.evo_num = evolutions
        self.dict_pull_init(name, target_lv)
        self.reset()
        # temp way to evolve
        while self.evo_num > 0:
            self.evo_num -= 1
            if self.evolution != 'None':
                self.dict_pull_init(self.evolution[0])

    def reset(self):
        self.dead = False
        self.statuses = []
        self.taru_minus = 0
        # tracking minuses in absolute value
        self.taru_plus = 0
        self.maka_minus = 0
        self.maka_plus = 0
        self.raku_minus = 0
        self.raku_plus = 0
        self.suku_minus = 0
        self.suku_plus = 0
        self.tetrakarn = False
        self.makarakarn = False
        self.tetraja = False
        self.focus = False
        if self.has_endure:
            self.endure = True
        else:
            self.endure = False

    def dict_pull_init(self, name, target_lv='None'):
        '''Subset of __init__ method for Demon classes; separate in order to call multiple times
        during evolution. Takes in name and optionally target level, sets the attributes:
        name, race, attack_changes, moves, passives, level, str, mag, vit,
        ag, luck, reflect, absorb, void, resist, weak, evolution, magatama. Also must call calc_init method
        to set hp, max_hp, mp, max_hp, and apply passives/attack changes.'''
        if name == 'None':
            possible_members = copy.deepcopy(list(demon_dict.keys()))
            random.shuffle(possible_members)
            for member in possible_members:
                party_check = True
                if self.party != 'None':
                    if member in self.party.list_demon_names():
                        party_check = False
                if party_check:
                    level_cap = False
                    if target_lv != 'None':
                        if demon_dict[member]['Level'] > target_lv + RANDOM_DEMON_RANGE:
                            level_cap = True
                        elif demon_dict[member]['Level'] < target_lv - RANDOM_DEMON_RANGE:
                            level_cap = True
                    if level_cap == False:
                        name, self.evo_num = find_evolve_count(member)
                        break
        self.name = name
        self.race = demon_dict[name]['Race']
        self.attack_changes = except_key(demon_dict, name, 'Attack', {})
        base_moves = except_key(demon_dict, name, 'Base Moves', [])
        for move in base_moves:
            if move in moves_dict and move not in self.move_names():
                self.moves.append(Move(move))
            if move in passives_dict and move not in self.passive_names():
                self.passives.append(Passive(move))
        # temp way to learn moves
        learned_moves = except_key(demon_dict, name, 'Learned Moves', [])
        for move in learned_moves:
            if move[0] in moves_dict and move[0] not in self.move_names():
                self.moves.append(Move(move[0]))
            if move[0] in passives_dict and move[0] not in self.passive_names():
                self.passives.append(Passive(move[0]))
        # shrink move pool to 8 by removing random moves
        if len(self.moves)+len(self.passives)-1 > 8: #-1 counts for attack
            removable_moves = []
            # prioritizes removing moves from past evolutions if possible
            for move in self.moves:
                if move.name not in base_moves and move.name not in [x[0] for x in learned_moves]:
                    removable_moves.append(move)
            for passive in self.passives:
                if passive.name not in base_moves and passive.name not in [x[0] for x in learned_moves]:
                    removable_moves.append(passive)
            # case where base demon has more than 8 moves
            if len(removable_moves) == 0:
                removable_moves = self.moves+self.passives
            removable_moves.remove(self.get_move('Attack'))
            random.shuffle(removable_moves)
            while len(self.moves)+len(self.passives)-1 > 8:
                removing_move = removable_moves.pop(0)
                if removing_move in self.moves:
                    self.moves.remove(removing_move)
                elif removing_move in self.passives:
                    self.passives.remove(removing_move)
        self.level = demon_dict[name]['Level']
        self.str = demon_dict[name]['Strength']
        self.mag = demon_dict[name]['Magic']
        self.vit = demon_dict[name]['Vitality']
        self.ag = demon_dict[name]['Agility']
        self.luck = demon_dict[name]['Luck']
        self.reflect = set(except_key(demon_dict, name, 'Reflect', []))
        self.absorb = set(except_key(demon_dict, name, 'Absorb', []))
        self.void = set(except_key(demon_dict, name, 'Void', []))
        self.resist = set(except_key(demon_dict, name, 'Resist', []))
        self.weak = set(except_key(demon_dict, name, 'Weaknesses', []))
        self.evolution = except_key(demon_dict, name, 'Evolution', 'None')
        self.magatama = 'None'
        self.calc_init()

    def calc_init(self):
        '''Subset of __init__ method for Demon classes; separate in order to call multiple times
        during evolution. Called during dict_pull_init subclass methods to set hp, max_hp,
        mp, max_hp, and apply passives/attack changes.'''
        self.hp = (self.level + self.vit) * 6
        if self.hp > 999:
            self.hp = 999
        self.max_hp = self.hp
        self.mp = (self.level + self.mag) * 3
        if self.mp > 999:
            self.mp = 999
        self.max_mp = self.mp
        for passive in self.passives:
            passive.init_apply(self)
        for move in self.moves:
            if move.name == 'Attack':
                for change_type, new_value in self.attack_changes.items():
                    if change_type == 'Element':
                        move.element = new_value
                    elif change_type == 'Hits':
                        move.hits = new_value
                        move.power = int(move.power / new_value)
                    if move.element != 'Phys' or move.element != 'Force':
                        del move.specials['Shatter']

    def heal(self):
        '''used in game resets; not intended for use during games'''
        self.reset()
        self.hp = self.max_hp
        self.mp = self.max_mp

    def level_up(self):
        print(f'{self.name} gained a level!')
        self.level += 1
        raisable_stats = []
        if self.str < 40:
            raisable_stats.append(self.str)
        if self.mag < 40:
            raisable_stats.append(self.mag)
        if self.vit < 40:
            raisable_stats.append(self.vit)
        if self.ag < 40:
            raisable_stats.append(self.ag)
        if self.luck < 40:
            raisable_stats.append(self.luck)
        if len(raisable_stats) >= 1:
            raised_stat = random.choice(raisable_stats)
        else:
            raised_stat = 'None'
        if raised_stat == self.str:
            print('Strength increased by 1!')
        elif raised_stat == self.mag:
            print('Magic increased by 1!')
        elif raised_stat == self.vit:
            print('Vitality increased by 1!')
        elif raised_stat == self.ag:
            print('Agility increased by 1!')
        elif raised_stat == self.luck:
            print('Luck increased by 1!')
        raised_stat += 1
        for move in demon_dict[self.name]['Learned Moves']:
            if self.level >= move[1]:
                if move[0] in moves_dict and move[0] not in self.move_names():
                    self.moves.append(Move(move[0]))
                    print(f'{self.name} learned {move[0]}!')
                if move[0] in passives_dict and move[0] not in self.passive_names():
                    self.passives.append(Passive(move[0]))
                    print(f'{self.name} learned {move[0]}!')
        print()
        if self.evolution != 'None':
            if self.level >= self.evolution[1]:
                print(f'{self.name} is evolving!')
                old_name = self.name
                # could put confirmation in here later, but rn that would suck to do each time
                self.dict_pull_init(self.evolution[0])
                print(f'{old_name} evolved into {self.name}!')

    def hp_percent(self):
        return self.hp / self.max_hp

    def get_move(self, move_name):
        for move in self.moves:
            if move.name == move_name:
                return move
        return False

    def move_names(self):
        return [move.name for move in self.moves]

    def passive_names(self):
        return [passive.name for passive in self.passives]

    def list_statuses(self):
        status_strings = []
        for status in self.statuses:
            status_strings.append(status.name)
        return status_strings

    def can_counter(self):
        counter = True
        if self.dead:
            counter = False
        else:
            for status in self.list_statuses():
                if status == 'Stone' or status == 'Stun' or status == 'Charm':
                    counter = False
                elif status == 'Bind' or status == 'Sleep' or status == 'Freeze' or status == 'Shock':
                    counter = False
        return counter

    def check_status_priority(self, status_name):
        can_apply = True
        for status in self.statuses:
            if status_list.index(status_name) > status_list.index(status.name):
                can_apply = False
        return can_apply

    def find_element_effect(self, element):
        '''called as a part of Move.calculate_element_effect. Separate for use in status calculation (which differs
        from normal moves)'''
        if element in self.reflect:
            return 'Reflect'
        elif element in self.absorb:
            return 'Absorb'
        elif element in self.void:
            return 'Void'
        elif element in self.weak:
            if element in self.resist:
                return 'Weak/Resist'
            return 'Weak'
        elif element in self.resist:
            return 'Resist'
        return 'Normal'

    def taru_total(self):
        return self.taru_plus - self.taru_minus

    def taru_mod(self):
        if self.taru_total() >= 0:
            return 1 + (0.25 * self.taru_total())
        else:
            return 1 + (0.125 * self.taru_total())

    def maka_total(self):
        return self.maka_plus - self.maka_minus

    def maka_mod(self):
        if self.maka_total() >= 0:
            return 1 + (0.25 * self.maka_total())
        else:
            return 1 + (0.125 * self.maka_total())

    def raku_total(self):
        return self.raku_plus - self.raku_minus

    def raku_mod(self):
        if self.raku_total() >= 0:
            return 1 + (0.25 * self.raku_total())
        else:
            return 1 + (0.125 * self.raku_total())

    def suku_total(self):
        return self.suku_plus - self.suku_minus

    def suku_mod(self):
        if self.suku_total() >= 0:
            return 1 + (0.25 * self.suku_total())
        else:
            return 1 + (0.125 * self.suku_total())

    def recover_hp(self, n):
        n = round(n)
        if self.hp + n > self.max_hp:
            recovered_hp = self.max_hp - self.hp
            self.hp = self.max_hp
        else:
            self.hp += n
            recovered_hp = n
        return recovered_hp

    def recover_mp(self, n):
        if self.mp + n > self.max_mp:
            recovered_mp = self.max_mp - self.mp
            self.mp = self.max_mp
        else:
            self.mp += n
            recovered_mp = n
        return recovered_mp

    def check_max(self):
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        if self.hp < 0:
            self.hp = 0
        if self.mp > self.max_mp:
            self.mp = self.max_mp
        if self.mp < 0:
            self.mp = 0

    def check_max_stats(self):
        no_adjust = True
        if self.str > 40:
            self.str = 40
            no_adjust = False
        if self.mag > 40:
            self.mag = 40
            no_adjust = False
        if self.vit > 40:
            self.vit = 40
            no_adjust = False
        if self.ag > 40:
            self.ag = 40
            no_adjust = False
        if self.luck > 40:
            self.luck = 40
            no_adjust = False
        return no_adjust

    def check_dead(self):
        if self.hp <= 0:
            if self.endure:
                self.endure = False
                print(f'{self.name} endured the attack!')
                self.hp = 1
                self.dead = False
            else:
                self.dead = True
        else:
            self.dead = False

    def check_max_buffs(self):
        no_adjust = True
        if self.taru_minus > 4:
            self.taru_minus = 4
            no_adjust = False
        if self.taru_plus > 4:
            self.taru_plus = 4
            no_adjust = False
        if self.maka_minus > 4:
            self.maka_minus = 4
            no_adjust = False
        if self.maka_plus > 4:
            self.maka_plus = 4
            no_adjust = False
        if self.raku_minus > 4:
            self.raku_minus = 4
            no_adjust = False
        if self.raku_plus > 4:
            self.raku_plus = 4
            no_adjust = False
        if self.suku_minus > 4:
            self.suku_minus = 4
            no_adjust = False
        if self.suku_plus > 4:
            self.suku_plus = 4
            no_adjust = False
        return no_adjust

    def effect_tarukaja(self):
        self.taru_plus += 1
        return self.check_max_buffs()

    def effect_makakaja(self):
        self.maka_plus += 1
        return self.check_max_buffs()

    def effect_rakukaja(self):
        self.raku_plus += 1
        return self.check_max_buffs()

    def effect_sukukaja(self):
        self.suku_plus += 1
        return self.check_max_buffs()

    def effect_tarunda(self):
        no_adjust = []
        self.taru_minus += 1
        if self.check_max_buffs():
            no_adjust.append(True)
        self.maka_minus += 1
        if self.check_max_buffs():
            no_adjust.append(True)
        if True in no_adjust:
            return True
        return False

    def effect_rakunda(self):
        self.raku_minus += 1
        return self.check_max_buffs()

    def effect_sukunda(self):
        self.suku_minus += 1
        return self.check_max_buffs()

    def clear_status(self, status_name):
        '''cure single status'''
        for status in self.statuses:
            if status.name == status_name:
                self.statuses.remove(status)
                return True
        return False

    def clear_statuses(self):
        '''for use when applying new effects'''
        for status_name in status_list:
            if status_name != 'Freeze' and status_name != 'Shock':
                self.clear_status(status_name)

    def tick_statuses(self):
        self.tetrakarn = False
        self.makarakarn = False
        for status in self.statuses:
            if status.tick(self):
                print(f'{self.name} recovered from {status.name}!\n')
                self.statuses.remove(status)

    def apply_poison_dmg(self):
        if 'Poison' in self.list_statuses():
            poison_dmg = round(self.max_hp / 8)
            if poison_dmg >= self.hp:
                poison_dmg = self.hp - 1
            self.hp -= poison_dmg
            if poison_dmg > 0:
                print(f'\n{self.name} took {poison_dmg} poison damage!')

    def mute_options(self, options):
        '''takes in list of options, if user is muted updates list in place to remove magic if muted and
        returns list of removed moves'''
        removed_moves = []
        if 'Mute' in self.list_statuses():
            for option in options:
                if option in moves_dict:
                    if moves_dict[option]['Category'] == 'Magic':
                        removed_moves.append(option)
        for removed_move in removed_moves:
            options.remove(removed_move)
        return removed_moves

    def charmed_options(self, options):
        removed_moves = []
        for option in options:
            if option in moves_dict:
                if 'Stock' in moves_dict[option]['Target'] or 'Dead' in moves_dict[option]['Target']:
                    removed_moves.append(option)
        for removed_move in removed_moves:
            options.remove(removed_move)
        return removed_moves

    def effect_conditions(self, condition):
        if condition == 'None':
            return True
        elif condition == 'Target Asleep':
            if 'Sleep' in self.list_statuses():
                return True
        elif condition == 'Target Poisoned':
            if 'Poison' in self.list_statuses():
                return True
        return False

    def proc_effect(self, effect, value):
        if effect == 'Cure Ailments':
            successful_cures = []
            for status in status_list:
                if self.clear_status(status):
                    successful_cures.append(status)
            for cured_status in successful_cures:
                print(f"{self.name} was cured of {cured_status}!")
            if len(successful_cures) == 0:
                print(f"{self.name} had no statuses to cure.")
        elif effect == 'Revive':
            self.hp = self.max_hp * value
            self.check_max()
            self.reset()
            print(f'{self.name} was revived with {self.hp} health!')
        elif effect == 'HP Recover':
            self.hp += round(self.max_hp * value)
            self.check_max()
            print(f'{self.name} gained {round(self.max_hp * value)} HP!')
        elif effect == 'MP Recover':
            self.mp += round(self.max_mp * value)
            self.check_max()
            print(f'{self.name} gained {round(self.max_mp * value)} MP!')
        elif effect == 'Share MP':
            self.mp += value
            self.check_max()
            print(f'{self.name} gained {value} MP!')
        elif effect == 'Tarukaja':
            if self.effect_tarukaja():
                print(f"{self.name}'s attack increased!")
            else:
                print(f"{self.name}'s attack maxed.")
        elif effect == 'Makakaja':
            if self.effect_makakaja():
                print(f"{self.name}'s magic increased!")
            else:
                print(f"{self.name}'s magic maxed.")
        elif effect == 'Rakukaja':
            if self.effect_rakukaja():
                print(f"{self.name}'s defense increased!")
            else:
                print(f"{self.name}'s defense maxed.")
        elif effect == 'Sukukaja':
            if self.effect_sukukaja():
                print(f"{self.name}'s accuracy/agility increased!")
            else:
                print(f"{self.name}'s agility maxed.")
        elif effect == 'Tarunda':
            if self.effect_tarunda():
                print(f"{self.name}'s physical/magic attacks weakened!")
            else:
                print(f"{self.name}'s attack power won't go lower.")
        elif effect == 'Rakunda':
            if self.effect_rakunda():
                print(f"{self.name}'s defense weakened!")
            else:
                print(f"{self.name}'s defense won't go lower.")
        elif effect == 'Sukunda':
            if self.effect_sukunda():
                print(f"Reduced {self.name}'s accuracy/agility!")
            else:
                print(f"{self.name}'s agility won't go lower.")
        elif effect == 'Fog Breath':
            successful_effects = []
            for i in range(2):
                successful_effects.append(self.effect_sukunda())
            if True in successful_effects:
                print(f"Reduced {self.name}'s accuracy/agility drastically!")
            else:
                print(f"{self.name}'s agility won't go lower.")
        elif effect == 'War Cry':
            successful_effects = []
            for i in range(2):
                successful_effects.append(self.effect_tarunda())
            if True in successful_effects:
                print(f"Weakened {self.name}'s physical/magic attacks drastically!")
            else:
                print(f"{self.name}'s attack power won't go lower.")
        elif effect == 'Debilitate':
            successful_lowers = []
            successful_lowers.append(self.effect_tarunda())
            successful_lowers.append(self.effect_rakunda())
            successful_lowers.append(self.effect_sukunda())
            if True in successful_lowers:
                print(f"{self.name}'s combat performance lowered!")
            else:
                print(f"{self.name}'s combat performance won't go lower.")
        elif effect == 'Taunt':
            successful_effects = []
            for i in range(2):
                successful_effects.append(self.effect_rakunda())
                successful_effects.append(self.effect_tarukaja())
            if True in successful_effects:
                print(f'{self.name} was enraged!')
            else:
                print(f"{self.name} can't be further enraged.")
        elif effect == 'Red Capote':
            successful_effects = []
            for i in range(2):
                successful_effects.append(self.effect_sukukaja())
            if True in successful_effects:
                print(f"{self.name}'s agility maximized!")
            else:
                print(f"{self.name}'s agility maxed.")
        elif effect == 'Dekunda':
            successful_null = False
            if self.taru_minus > 0:
                self.taru_minus = 0
                successful_null = True
            if self.maka_minus > 0:
                self.maka_minus = 0
                successful_null = True
            if self.raku_minus > 0:
                self.raku_minus = 0
                successful_null = True
            if self.suku_minus > 0:
                self.suku_minus = 0
                successful_null = True
            if successful_null:
                print(f"{self.name}'s -nda effects cancelled!")
            else:
                print(f"{self.name} had no debuffs to cancel.")
        elif effect == 'Dekaja':
            successful_null = False
            if self.taru_plus > 0:
                self.taru_plus = 0
                successful_null = True
            if self.maka_plus > 0:
                self.maka_plus = 0
                successful_null = True
            if self.raku_plus > 0:
                self.raku_plus = 0
                successful_null = True
            if self.suku_plus > 0:
                self.suku_plus = 0
                successful_null = True
            if successful_null:
                print(f"{self.name}'s -kaja effects cancelled!")
            else:
                print(f"{self.name} had no buffs to cancel.")
        elif effect == 'Reflect Magic':
            self.makarakarn = True
            print(f'{self.name} gained a magic-repelling barrier!')
        elif effect == 'Reflect Phys':
            self.tetrakarn = True
            print(f'{self.name} gained a physical-repelling barrier!')
        elif effect == 'Void Expel/Death':
            self.tetraja = True
            print(f'{self.name} gained an anti-expel/death shield!')
        elif effect == 'Focus':
            self.focus = True
            print(f'{self.name} is focusing for a powerful attack!')
        elif effect == 'Freeze':
            if 'Shock' not in self.list_statuses() and 'Freeze' not in self.list_statuses():
                self.statuses.append(Status('Freeze'))
                print(f'{self.name} was frozen!')
        elif effect == 'Shock':
            if 'Shock' not in self.list_statuses() and 'Freeze' not in self.list_statuses():
                self.statuses.append(Status('Shock'))
                print(f'{self.name} was shocked!')
        elif effect == 'Charm':
            if self.check_status_priority('Charm'):
                self.clear_statuses()
                self.statuses.append(Status('Charm'))
                print(f'{self.name} was charmed!')
        elif effect == 'Stun':
            if self.check_status_priority('Stun'):
                self.clear_statuses()
                self.statuses.append(Status('Stun'))
                print(f'{self.name} was stunned!')
        elif effect == 'Cure Stun':
            if self.clear_status('Stun'):
                print(f"{self.name} was cured of stun!")
            else:
                print(f"{self.name} was not stunned.")
        elif effect == 'Poison':
            if self.check_status_priority('Poison'):
                self.clear_statuses()
                self.statuses.append(Status('Poison'))
                print(f'{self.name} was poisoned!')
        elif effect == 'Cure Poison':
            if self.clear_status('Poison'):
                print(f"{self.name} was cured of poison!")
            else:
                print(f"{self.name} was not poisoned.")
        elif effect == 'Mute':
            if self.check_status_priority('Mute'):
                self.clear_statuses()
                self.statuses.append(Status('Mute'))
                print(f'{self.name} was muted!')
        elif effect == 'Cure Mute':
            if self.clear_status('Mute'):
                print(f"{self.name} was cured of mute!")
            else:
                print(f"{self.name} was not muted.")
        elif effect == 'Bind':
            if self.check_status_priority('Bind'):
                self.clear_statuses()
                self.statuses.append(Status('Bind'))
                print(f'{self.name} was bound!')
        elif effect == 'Panic':
            if self.check_status_priority('Panic'):
                self.clear_statuses()
                self.statuses.append(Status('Panic'))
                print(f'{self.name} was panicked!')
        elif effect == 'Sleep':
            if self.check_status_priority('Sleep'):
                self.clear_statuses()
                self.statuses.append(Status('Sleep'))
                print(f'{self.name} was put to sleep!')
        elif effect == 'Cure Bind/Sleep/Panic':
            successful_cures = []
            for status in ['Bind', 'Sleep', 'Panic']:
                if self.clear_status(status):
                    successful_cures.append(status)
            for cured_status in successful_cures:
                print(f"{self.name} was cured of {cured_status}!")
            if len(successful_cures) == 0:
                print(f"{self.name} had no statuses to cure.")
        elif effect == 'Stone':
            if self.check_status_priority('Stone'):
                self.clear_statuses()
                self.statuses.append(Status('Stone'))
                print(f'{self.name} was petrified!')
        elif effect == 'Cure Stone':
            if self.clear_status('Stone'):
                print(f"{self.name} was cured of stone!")
            else:
                print(f"{self.name} was not stone.")
        elif effect == 'Kill':
            self.hp = 0
        elif effect == 'Reduce HP':
            self.hp = round(self.hp * value)
            print(f"{self.name}'s HP cut by {(1 - value) * 100}%!")
        elif effect == 'One HP':
            self.hp = 1
            print(f"{self.name}'s HP was brought to 1!")
        elif effect == 'Shatter':
            if 'Stone' in self.list_statuses():
                self.hp = 0
                print(f'{self.name} was shattered!')
        elif effect == 'Summon':
            print(f'{self.name} was summoned to the battlefield!')
            self.party.summon(self)
        elif effect == 'Analyze':
            print(f'Analyzing {self.name}...')
            print(self)
            self.analyzed = True
        else:
            print('Effect missing.')

    def choose_target(self, decision_move, party, other_party):
        '''make sure returns list, even for single target'''
        valid_decision = False
        break_counter = 0
        while valid_decision == False:
            if decision_move.target == 'Single Enemy':
                print(f'{decision_move.name} will target a single enemy.')
                if len(other_party) >= 1:
                    target_string = f'Valid targets: '
                    i = 1
                    if len(other_party) > 1:
                        for demon in other_party.demons[:-1]:
                            target_string += f'[{i}] {demon.name} (HP: {demon.hp}/{demon.max_hp}), '
                            i += 1
                    if len(other_party) >= 1:
                        target_string += f'[{i}] {other_party.demons[-1].name} '
                        target_string += f'(HP: {other_party.demons[-1].hp}/{other_party.demons[-1].max_hp})\n'
                    else:
                        target_string += 'None\n'
                    print(target_string)
                    # can change to "type desired demon" once enough functional ones are added?
                    target_decision = h_input('Choose a target number or type "back": ', 'Target Selection').lower()
                    print()
                    if target_decision == 'back':
                        return 'back'
                    else:
                        try:
                            target_decision = int(target_decision)
                            if target_decision >= 1 and target_decision <= len(other_party):
                                target_list = []
                                for i in range(decision_move.hits):
                                    target_list.append(other_party.demons[target_decision - 1])
                                return target_list
                        except ValueError:
                            pass
                else:
                    print('There are no valid targets.\n')
                    return 'back'
                print('Invalid input. Please try again.')
            elif decision_move.target == 'All Enemies':
                print(f'{decision_move.name} will target all enemies.')
                input_str = 'Type "back" to return or type anything else to continue: '
                target_decision = h_input(input_str, 'Target Selection').lower()
                print()
                if target_decision == 'back':
                    return 'back'
                else:
                    target_list = []
                    for demon in other_party.demons:
                        for i in range(decision_move.hits):
                            target_list.append(demon)
                    return target_list
            elif decision_move.target == 'Self':
                print(f'{decision_move.name} will target {self.name}.')
                input_str = 'Type "back" to return or type anything else to continue: '
                target_decision = h_input(input_str, 'Target Selection').lower()
                print()
                if target_decision == 'back':
                    return 'back'
                else:
                    return [self]
            elif decision_move.target == 'Single Ally':
                print(f'{decision_move.name} will target a single ally.')
                if len(party) >= 1:
                    target_string = f'Valid targets: '
                    i = 1
                    if len(party) > 1:
                        for demon in party.demons[:-1]:
                            target_string += f'[{i}] {demon.name} (HP: {demon.hp}/{demon.max_hp}), '
                            i += 1
                    target_string += f'[{i}] {party.demons[-1].name} '
                    target_string += f'(HP: {party.demons[-1].hp}/{party.demons[-1].max_hp})\n'
                    print(target_string)
                    target_decision = h_input('Choose a target number or type "back": ', 'Target Selection').lower()
                    print()
                    if target_decision == 'back':
                        return 'back'
                    else:
                        try:
                            target_decision = int(target_decision)
                            if target_decision >= 1 and target_decision <= len(party):
                                return [party.demons[target_decision - 1]]
                        except ValueError:
                            pass
                else:
                    print('There are no valid targets.\n')
                    return 'back'
                print('Invalid input. Please try again.')
            elif decision_move.target == 'Other Allies':
                print(f'{decision_move.name} will target all other allies.')
                input_str = 'Type "back" to return or type anything else to continue: '
                target_decision = h_input(input_str, 'Target Selection').lower()
                print()
                if target_decision == 'back':
                    return 'back'
                else:
                    demon_list = []
                    for demon in party.demons:
                        if demon != self:
                            demon_list.append(demon)
                    return demon_list
            elif decision_move.target == 'All Allies':
                print(f'{decision_move.name} will target all allies.')
                input_str = 'Type "back" to return or type anything else to continue: '
                target_decision = h_input(input_str, 'Target Selection').lower()
                print()
                if target_decision == 'back':
                    return 'back'
                else:
                    return party.demons
            elif decision_move.target == "Random Enemies":
                print(f'{decision_move.name} will target random enemies.')
                input_str = 'Type "back" to return or type anything else to continue: '
                target_decision = h_input(input_str, 'Target Selection').lower()
                print()
                if target_decision == 'back':
                    return 'back'
                else:
                    return other_party.random_targets(decision_move.hits)
            elif decision_move.target == 'Dead Ally':
                print(f'{decision_move.name} will target a dead demon in your stock.')
                if len(party.dead_demons()) >= 1:
                    target_string = 'Valid targets: '
                    i = 1
                    if len(party.dead_demons()) > 1:
                        for demon in party.dead_demons()[:-1]:
                            target_string += f'[{i}] {demon.name}, '
                            i += 1
                    target_string += f'[{i}] {party.dead_demons()[-1].name}'
                    print(target_string)
                    target_decision = h_input('Choose a target number or type "back": ', 'Target Selection').lower()
                    print()
                    if target_decision == 'back':
                        return 'back'
                    else:
                        try:
                            target_decision = int(target_decision)
                            if 1 <= target_decision <= len(party.dead_demons()):
                                return [party.dead_demons()[target_decision - 1]]
                        except ValueError:
                            pass
                else:
                    print('There are no valid targets.\n')
                    return 'back'
                print('Invalid input. Please try again.')
            elif decision_move.target == 'Stock Ally':
                print(f'{decision_move.name} will target a demon in your stock.')
                if len(party.summonable_demons()) >= 1:
                    target_string = f'Valid targets: '
                    i = 1
                    if len(party.summonable_demons()) > 1:
                        for demon in party.summonable_demons()[:-1]:
                            target_string += f'[{i}] {demon.name} (HP: {demon.hp}/{demon.max_hp}), '
                            i += 1
                    target_string += f'[{i}] {party.summonable_demons()[-1].name} '
                    target_string += f'(HP: {party.summonable_demons()[-1].hp}'
                    target_string += f'/{party.summonable_demons()[-1].max_hp})\n'
                    print(target_string)
                    target_decision = h_input('Choose a target number or type "back": ', 'Target Selection').lower()
                    print()
                    if target_decision == 'back':
                        return 'back'
                    else:
                        try:
                            target_decision = int(target_decision)
                            if 1 <= target_decision <= len(party.summonable_demons()):
                                return [party.summonable_demons()[target_decision - 1]]
                        except ValueError:
                            pass
                else:
                    print('There are no valid targets.\n')
                    return 'back'
                print('Invalid input. Please try again.')
            elif decision_move.target == 'Random Stock Ally':
                print(f'{decision_move.name} will target a random demon in your stock.')
                if len(party.summonable_demons()) >= 1:
                    input_str = 'Type "back" to return or type anything else to continue: '
                    target_decision = h_input(input_str, 'Target Selection').lower()
                    print()
                    if target_decision == 'back':
                        return 'back'
                    else:
                        return [random.choice(party.summonable_demons())]
                else:
                    print('There are no valid targets.\n')
                    return 'back'
            elif decision_move.target == 'Lowest HP':
                all_demons = party.demons + other_party.demons
                random.shuffle(all_demons)
                all_demons.sort(key=operator.methodcaller('hp_percent'))
                output = f'{decision_move.name} will target the demon with the lowest %HP. '
                output += f'Currently, this is {all_demons[0].name}.'
                print(output)
                input_str = 'Type "back" to return or type anything else to continue: '
                target_decision = h_input(input_str, 'Target Selection').lower()
                print()
                if target_decision == 'back':
                    return 'back'
                else:
                    return [all_demons[0]]
            break_counter += 1
            if break_counter >= 255:
                print('Unable to select target.')
                return 'back'

    def use_move(self, move, target, kagutsuchi=Kagutsuchi('Dead'), input_hit='Unknown', input_crit='Unknown'):
        press_turns = 1
        damage_dealt = 0
        counter_possible = False
        move_hit = True
        move_crit = False
        might_crit = False
        for passive in self.passives:
            passive.attack_apply(move)
        if 'Stone' in target.list_statuses() and move.element in ['Fire', 'Ice', 'Elec']:
            move.temp_dmg_factor *= 1 / 10
        if 'Poison' in self.list_statuses() and move.category == 'Physical':
            move.temp_dmg_factor *= 1 / 2
        if self.focus and move.category == 'Physical':
            move.temp_dmg_factor *= 2.5
            self.focus = False
        # check for dodge
        if input_hit != True:
            if input_hit == False or move.calculate_accuracy(self, target) < random.randint(1, 100):
                move_hit = False
                print(f'{target.name} dodged the attack!')
                press_turns = 2
        if move_hit != False:
            # set resistances/weaknesses
            element_effect, barrier_effect, barrier = move.calculate_element_effect(target)
            if barrier == 'Tetrakarn':
                target.tetrakarn = False
            elif barrier == 'Makarakarn':
                target.makarakarn = False
            elif barrier == 'Tetraja':
                target.tetraja = False
            # initiate reverse object for reflect
            if element_effect == 'Reflect' or barrier_effect == 'Reflect':
                if barrier_effect == 'Reflect':
                    print(f"{target.name}'s shield reflected the attack!")
                else:
                    print(f'{target.name} reflected the attack!')
                move.reflected = True
                reflect_move_info = self.use_move(move, self, input_hit, input_crit)
                if reflect_move_info['Crit'] == True:
                    move_crit = True
                press_turns = 'All'
            else:
                # damaging moves + heals
                if move.power != 'None' or 'Heal' in move.specials:
                    damage = move.calculate_base_damage(self, target)
                    damage *= random.randint(1000, 1100) / 1000
                    damage *= move.temp_dmg_factor
                    if input_crit != False:
                        if input_crit == True or move.calculate_crit(self, target, kagutsuchi):
                            move_crit = True
                            # print passive statements for crits
                            # bright/dark might prints would fit better in move.calculate_crit
                            # they are here so that calculate_crit only returns, doesn't print anything
                            # rn, testing more than once for bright might activation
                            # could set crit=true here?
                            if move.name == 'Attack':
                                if 'Bright Might' in self.passive_names() and kagutsuchi == 8:
                                    print(f"{self.name}'s Bright Might activated!")
                                elif 'Dark Might' in self.passive_names() and kagutsuchi == 0:
                                    print(f"{self.name}'s Dark Might activated!")
                                elif 'Might' in self.passive_names():
                                    print(f"{self.name}'s Might activated!")
                            print('Critical hit!')
                            damage *= 3 / 2
                            press_turns = 0.5
                    element_coefficient = 1
                    if barrier_effect == 'Void':
                        element_coefficient = 0
                        print(f"{target.name}'s shield voided the attack!")
                        press_turns = 2
                    elif element_effect == 'Absorb':
                        if move.pierce:
                            print('Pierced!')
                        else:
                            element_coefficient = -1
                            print(f'{target.name} absorbed the attack!')
                            press_turns = 'All'
                    elif element_effect == 'Void':
                        if move.pierce:
                            print('Pierced!')
                        else:
                            element_coefficient = 0
                            print(f'{target.name} voided the attack!')
                            press_turns = 2
                    elif element_effect == 'Weak':
                        element_coefficient = 1.5
                        print(f'{target.name} was weak to the attack!')
                        press_turns = 0.5
                    elif element_effect == 'Weak/Resist':
                        if move.pierce:
                            element_coefficient = 1.5
                            print('Pierced!')
                        else:
                            element_coefficient = 0.75
                        print(f'{target.name} was weak to the attack!')
                        press_turns = 0.5
                    elif element_effect == 'Resist':
                        if move.pierce:
                            print('Pierced!')
                        else:
                            element_coefficient = 0.5
                            print(f'{target.name} resisted the attack!')
                    damage = round(damage * element_coefficient)
                    if 'Heal' in move.specials:
                        damage *= -1
                    deal_regular_damage = True
                    if 'MP Drain' in move.specials:
                        power_factor = move.specials['MP Drain']['Value']
                        mp_damage = move.calculate_base_damage(self, target, power_factor)
                        mp_damage *= random.randint(1000, 1100) / 1000
                        mp_damage = round(mp_damage * move.temp_dmg_factor)
                        if mp_damage < 0:
                            mp_damage = 0
                        if target.mp < mp_damage:
                            mp_damage = target.mp
                        self.mp += mp_damage
                        target.mp -= mp_damage
                        print(f'{self.name} drained {mp_damage} MP!')
                        print(f'{target.name} lost {mp_damage} MP!')
                        # MP draining moves only continue if also HP draining
                        # inflexible: regular moves can't regain MP
                        # sufficient for all possible moves?
                        if 'HP Drain' not in move.specials:
                            deal_regular_damage = False
                    if deal_regular_damage:
                        if target.hp < damage:
                            real_damage_dealt = target.hp
                        else:
                            real_damage_dealt = damage
                        target.hp -= damage
                        if damage > 0:
                            print(f'{target.name} took {damage} damage!')
                            # cure sleep
                            if target.clear_status('Sleep'):
                                print(f'{target.name} recovered from Sleep!')
                            # check if counter could occur (initialize at end of init move)
                            if move.category == 'Physical' and move.reflected == False:
                                # going to have to add other immobilizing statuses
                                if 'Freeze' not in target.list_statuses() and 'Shock' not in target.list_statuses():
                                    counter_possible = True
                        elif damage < 0:
                            if 'Heal' in move.specials and real_damage_dealt == 0:
                                print(f"{target.name}'s health is full.")
                            print(f'{target.name} gained {-damage} health!')
                        elif damage == 0:
                            if 'Heal' in move.specials:
                                print(f"{target.name}'s health is full.")
                            else:
                                print(f'{target.name} took no damage!')
                        if 'HP Drain' in move.specials:
                            hp_damage = round(real_damage_dealt * move.specials['HP Drain']['Value'])
                            if hp_damage < 0:
                                hp_damage = 0
                            if might_crit == False:
                                self.hp += hp_damage
                                if hp_damage > 0:
                                    print(f'{self.name} drained {hp_damage} HP!')
                                self.check_max()
                else:
                    damage = 'None'
                # special effects
                if len(move.specials) > 0:
                    parent_null = False
                    one_proc = False
                    # check elemental effect of base move
                    if damage != 'None':
                        if element_effect == 'Absorb' or element_effect == 'Void':
                            parent_null = True
                    if parent_null == False:
                        tetraja_status_shield = False
                        for effect, effect_info in copy.deepcopy(move.specials).items():
                            if effect_info['Target'] == 'Same':
                                # could improve how prints are initiated— somewhat inflexible?
                                # should be sufficient for all existing moves
                                # would be wrong if there were two effects with different elements
                                chance_factor = 1
                                effect_weak = False
                                temp_element_effect = target.find_element_effect(effect_info['Element'])
                                if barrier_effect == 'Void':
                                    chance_factor *= 0
                                    tetraja_status_shield = True
                                elif target.tetraja:
                                    if effect_info['Element'] == 'Expel' or effect_info['Element'] == 'Death':
                                        chance_factor *= 0
                                        tetraja_status_shield = True
                                elif temp_element_effect == 'Reflect' or element_effect == 'Absorb':
                                    chance_factor *= 0
                                    if damage == 'None':
                                        press_turns = 'All'
                                        print(f'{target.name} voided the attack!')
                                elif temp_element_effect == 'Void':
                                    chance_factor *= 0
                                    if damage == 'None':
                                        press_turns = 2
                                        print(f'{target.name} voided the attack!')
                                elif temp_element_effect == 'Weak':
                                    chance_factor *= 1.5
                                    effect_weak = True
                                elif temp_element_effect == 'Weak/Resist':
                                    chance_factor *= 0.75
                                    effect_weak = True
                                elif temp_element_effect == 'Resist':
                                    chance_factor *= 0.5
                                if target.magatama != 'None':
                                    if effect == 'Kill':
                                        if effect_info['Element'] == 'Expel' or effect_info['Element'] == 'Death':
                                            chance_factor *= 0.5
                                effect_chance = effect_info['Accuracy']
                                effect_miss = False
                                if effect != 'Heal' and 'Drain' not in effect and 'Might' not in effect:
                                    if effect_chance < 100 or chance_factor == 0:
                                        effect_chance *= chance_factor
                                    if effect_chance >= random.randint(1, 100):
                                        if target.effect_conditions(effect_info['Condition']):
                                            if effect_weak and one_proc == False:
                                                if move.power == 'None':
                                                    print(f'{target.name} was weak to the attack!')
                                                    press_turns = 0.5
                                            target.proc_effect(effect, effect_info['Value'])
                                            one_proc = True
                                        else:
                                            effect_miss = True
                                    else:
                                        effect_miss = True
                                    if effect_miss:
                                        if move.power == 'None' and effect_chance != 0:
                                            if tetraja_status_shield == False:
                                                print(f'The effect missed {target.name}!')
                        if tetraja_status_shield:
                            print(f"{target.name}'s shield voided the effects!")
                            target.tetraja = False
                target.check_max()
                self.check_max()
                if move.reflected == False:
                    # checking if reflected b/c og user will finish using move before dying
                    target.check_dead()
                    if target.dead:
                        print(f'{target.name} died!')
        move.reset()
        return {'Press Turns': press_turns, 'Counter': counter_possible, 'Hit': move_hit, 'Crit': move_crit}

    def initiate_move(self, move, target, other_party, kagutsuchi=Kagutsuchi('Dead'), charmed=False):
        # other_party needed for multihit retargeting
        '''returns press turns'''
        print('******************************************************************')
        print(f'{self.name} used {move.name}!')
        self.mp -= move.mp
        self.hp -= move.hp_cost(self)
        press_turns = []
        possible_counters = []
        moves_initiated = 0
        move_hit = 'Unknown'
        move_crit = 'Unknown'
        # main
        for demon in target:
            if demon.dead == False or 'Dead' in move.target:
                print()
                moves_initiated += 1
                index_from_end = moves_initiated - target.index(demon)
                move_outputs = self.use_move(move, demon, kagutsuchi, move_hit, move_crit)
                press_turns.append(move_outputs['Press Turns'])
                if move_outputs['Counter']:
                    possible_counters.append(demon)
                # for standardizing single-target multi-hit accuracy/crit
                if move.hits > 1:
                    if move.target == 'Single Enemy' or move.target == 'All Enemies':
                        if target[:moves_initiated].count(demon) < move.hits:
                            move_hit = move_outputs['Hit']
                            move_crit = move_outputs['Crit']
                        else:
                            move_hit = 'Unknown'
                            move_crit = 'Unknown'
            # redirect multihits to other demons
            elif move.target == 'Random Enemies':
                new_targets = []
                for new_demon in other_party.demons:
                    if new_demon.dead == False and target.count(new_demon) < 2:
                        new_targets.append(new_demon)
                if len(new_targets) >= 1:
                    print()
                    new_target = random.choice(new_targets)
                    # could replace new_target with random.choice in use_move call
                    # separated for debugging
                    move_outputs = self.use_move(move, new_target)
                    press_turns.append(move_outputs['Press Turns'])
                    if move_outputs['Counter']:
                        possible_counters.append(demon)
        # add different-targeting effects
        for effect, effect_info in move.specials.items():
            if effect_info['Target'] == 'Self':
                print()
                if effect == 'HP Recover':
                    temp_move = Move('Life Stone')
                    temp_move.specials['HP Recover']['Value'] = effect_info['Value']
                    # do we care about outputs?
                    self.use_move(temp_move, self)
                elif effect == 'MP Recover':
                    temp_move = Move('Chakra Drop')
                    temp_move.specials['MP Recover']['Value'] = effect_info['Value']
                    self.use_move(temp_move, self)
                elif effect == 'Kill':
                    self.hp = 0
                else:
                    print('Effect missing.')

        # check if user died (to reflects)
        self.check_dead()
        if self.dead == False and not charmed:
            # initialize counters here
            # needed b/c only one per demon, after og move has finished
            for demon in set(possible_counters):
                if self.dead:
                    break
                elif demon.can_counter():
                    for passive in demon.passives:
                        if random.randint(0, 1) == 1:
                            passive.counter_apply(demon, self, kagutsuchi)
                            self.check_dead()
                            break  # should be necessary to stop multiple counters from triggering
            self.apply_poison_dmg()
        if self.dead:
            print(f'{self.name} died!')
        print('******************************************************************\n')
        # scans for relevant press turn value to return
        if 'All' in press_turns:
            return 'All'
        elif 2 in press_turns:
            return 2
        elif 0.5 in press_turns:
            return 0.5
        elif 1 in press_turns:
            return 1
        # catches case where recarmdra has no targets; press_turns is empty
        # would this break anything else?
        elif len(press_turns) == 0:
            return 1

    def choose_target_easy(self, decision_move, party, other_party):
        '''takes in decision as Move'''
        if decision_move.target == 'Single Enemy':
            return [random.choice(other_party.demons)]
        elif decision_move.target == 'All Enemies':
            return other_party.demons
        elif decision_move.target == 'Self':
            return [self]
        elif decision_move.target == 'Single Ally':
            return [random.choice(party.demons)]
        elif decision_move.target == 'Other Allies':
            demon_list = []
            for demon in party.demons:
                if demon != self:
                    demon_list.append(demon)
            return demon_list
        elif decision_move.target == 'All Allies':
            return party.demons
        elif decision_move.target == 'Random Enemies':
            return other_party.random_targets(decision_move.hits)
        elif decision_move.target == 'Dead Ally':
            return [random.choice(party.dead_demons())]
        elif decision_move.target == 'Stock Ally':
            return [random.choice(party.summonable_demons())]
        elif decision_move.target == 'Random Stock Ally':
            return [random.choice(party.summonable_demons())]
        elif decision_move.target == 'Lowest HP':
            all_demons = party.demons + other_party.demons
            random.shuffle(all_demons)
            all_demons.sort(key=operator.methodcaller('hp_percent'))
            return [all_demons[0]]
        else:
            print('Unable to select target.')
            return 'back'

    def choose_move_easy(self, party, other_party, charmed=False):
        possible_moves = self.move_names()
        # mute effect
        self.mute_options(possible_moves)
        # charm effect
        if charmed:
            self.charmed_options(possible_moves)
        valid_move = False
        while valid_move == False:
            try:
                decision = possible_moves.pop(random.randint(0, len(possible_moves) - 1))
            except ValueError:
                return 'Pass'
            if decision in moves_dict:
                decision_move = Move(decision)
                if decision_move.mp <= self.mp and decision_move.hp_cost(self) < self.hp:
                    valid_targets = True
                    if 'Enemies' in decision_move.target or 'Enemy' in decision_move.target:
                        if len(other_party) < 1:
                            valid_targets = False
                    if 'Stock' in decision_move.target:
                        if len(party.summonable_demons()) < 1:
                            valid_targets = False
                    if 'Dead' in decision_move.target:
                        if len(party.dead_demons()) < 1:
                            valid_targets = False
                    if valid_targets:
                        return decision_move.name


    def choose_move_hard(self, party, other_party):
        '''placeholder; not yet implemented'''
        return self.choose_move_easy(party, other_party)


    def action(self, party, other_party, controller, kagutsuchi=Kagutsuchi('Dead')):
        valid_decision = False
        while valid_decision == False:
            print(f'Current demon: {self.name} HP: {self.hp}/{self.max_hp} MP: {self.mp}/{self.max_mp}')
            #for charm effect: needs to be global to check after action ends
            turn_against_party = False
            # stone effect
            if 'Stone' in self.list_statuses():
                print(f'\n{self.name} is petrified...')
                return 1
            # charm effect
            elif 'Charm' in self.list_statuses():
                charm_test_party = copy.deepcopy(party)
                charm_test_party.demons.pop()
                if random.randint(0, 1) == 1 and self.choose_move_easy(other_party, charm_test_party) != False:
                    print(f'\n{self.name} turned against the party!')
                    turn_against_party = True
                    temp_party = party
                    party = other_party
                    other_party = temp_party
                    other_party.remove_demon(self)
                    controller = 'Easy'
                else:
                    print(f'\n{self.name} is acting strangely...\n')
                    return 1
            # bind effect
            elif 'Bind' in self.list_statuses():
                print(f'\n{self.name} is bound!\n')
                return 1
            # panic effect
            elif 'Panic' in self.list_statuses():
                panic_actions = 4
                if self.magatama != 'None':
                    panic_actions = 3
                random_panic_action = random.randint(1, panic_actions)
                print(f'\n{self.name} is panicked...')
                # 1: normal action
                if random_panic_action == 2:
                    # add macca dropping action
                    print(f'\n{self.name} dropped some Macca!')
                    return 1
                elif random_panic_action == 3:
                    # add real convo initiate
                    print(f'\n{self.name} started babbling to {random.choice(other_party.demons).name}!')
                    return 1
                elif random_panic_action == 4:
                    print(f'\n{self.name} retreated!\n')
                    party.unsummon(self)
                    return 1
            # sleep effect
            elif 'Sleep' in self.list_statuses():
                print(f'\n{self.name} is asleep...')
                recovered_hp = self.recover_hp(self.max_hp / 8)
                if recovered_hp > 0:
                    print(f'{self.name} recovered {recovered_hp} HP.')
                recovered_mp = self.recover_mp(self.max_mp / 8)
                if recovered_mp > 0:
                    print(f'{self.name} recovered {recovered_mp} MP.')
                print()
                return 1
            if controller == 'Player':
                options = ['Pass', 'View', 'Stop']
                options += self.move_names()
                # mute effect
                muted_moves = self.mute_options(options)
                if len(muted_moves) >= 1:
                    print(f"{self.name} is unable to cast spells!")
                for demon in party.demons:
                    if demon == self:
                        options.append(f'View Self')
                    else:
                        options.append(f'View {demon.name}')
                    for move in demon.move_names():
                        options.append(f'View {move}')
                    for move in demon.passive_names():
                        options.append(f'View {move}')
                for demon in other_party.demons:
                    options.append(f'View {demon.name}')
                    for move in demon.move_names():
                        options.append(f'View {move}')
                    for move in demon.passive_names():
                        options.append(f'View {move}')
                for i in range(1, len(party) + len(other_party) + 1):
                    options.append(f'View {i}')
                options = list(set(options))
                move_list_string = 'Your options: '
                for move in self.moves:
                    if move.name not in muted_moves:
                        move_list_string += f'{move.name} ({move.user_cost_string(self)}), '
                move_list_string += 'Pass\n'
                print(move_list_string)
                decision = ''
                temp_decision = h_input('What will you do? ', 'Move Selection').title()
                if temp_decision != '':
                    closest_matches = process.extract(temp_decision, options, limit=None)
                    # isolate view commands based on input
                    if temp_decision[:4] == 'View':
                        new_closest_matches = copy.deepcopy(closest_matches)
                        for option in closest_matches:
                            if option[0][:4] != 'View':
                                new_closest_matches.remove(option)
                        closest_matches = new_closest_matches
                    else:
                        new_closest_matches = copy.deepcopy(closest_matches)
                        for option in closest_matches:
                            if option[0][:4] == 'View':
                                new_closest_matches.remove(option)
                        closest_matches = new_closest_matches
                    # decide if able
                    if closest_matches[0][1] > 70 and closest_matches[0][1] != closest_matches[1][1]:
                        decision = closest_matches[0][0]
            elif controller == 'Easy':
                print()
                decision = self.choose_move_easy(party, other_party, turn_against_party)
            elif controller == 'Hard':
                print()
                if turn_against_party:
                    decision = self.choose_move_easy(party, other_party, turn_against_party)
                else:
                    decision = self.choose_move_hard(party, other_party)
            else:
                raise ValueError(f"Unrecognized controller: {controller}")
            # analyze decisions
            if decision == 'Stop':
                return 'Stop'
            elif decision[:4] == 'View':
                if decision == 'View':
                    print('\nYour party:')
                    party.quick_view()
                    print('\nEnemy party:')
                    other_party.quick_view(len(party) + 1)
                    view_explain_str = "\nTo view a specific demon's details, type "
                    view_explain_str += '"view {demon}", '
                    view_explain_str += "or to view a move's details, type "
                    view_explain_str += '"view {move}".\n'
                    print(view_explain_str)
                elif decision[5:] in moves_dict:
                    show_move = False
                    for demon in party.demons:
                        if decision[5:] in demon.move_names():
                            show_move = True
                    for demon in other_party.demons:
                        if decision[5:] in demon.move_names() and demon.analyzed:
                            show_move = True
                    if show_move:
                        print('\n' + str(Move(decision[5:])))
                    else:
                        print('\n' + Move(decision[5:]).unknown_str())
                elif decision[5:] in passives_dict:
                    show_move = False
                    for demon in party.demons:
                        if decision[5:] in demon.passive_names():
                            show_move = True
                    for demon in other_party.demons:
                        if decision[5:] in demon.passive_names() and demon.analyzed:
                            show_move = True
                    if show_move:
                        print('\n' + str(Passive(decision[5:])))
                    else:
                        print('\n' + Passive(decision[5:]).unknown_str())
                elif decision[5:] == 'Self':
                    print('\n' + str(self))
                elif decision[5:].isnumeric():
                    # search for demon on battlefield by number
                    demon_search_index = int(decision[5:])
                    searching_party = party
                    if demon_search_index > len(party):
                        searching_party = other_party
                        demon_search_index -= len(party)
                    viewing_demon = searching_party.demons[demon_search_index - 1]
                    if searching_party == party or viewing_demon.analyzed:
                        print('\n' + str(viewing_demon))
                    else:
                        print('\n' + viewing_demon.unknown_str())
                elif decision[5:] in master_list or decision[5:] == 'Demi-Fiend':
                    # search for demon(s) on battlefield by name
                    viewed_demons = []
                    all_demons = party.demons + other_party.demons
                    for demon in all_demons:
                        if decision[5:] == demon.name:
                            viewed_demons.append(demon)
                    view_demon_str = '\n'
                    if len(viewed_demons) > 1:
                        view_demon_str += f'{len(viewed_demons)} demons have the name {decision[5:]}:\n\n'
                    for demon in viewed_demons:
                        if demon in party.demons or demon.analyzed:
                            view_demon_str += str(demon) + '\n'
                        else:
                            view_demon_str += demon.unknown_str() + '\n'
                    view_demon_str = view_demon_str[:-1]
                    print(view_demon_str)
            elif decision == 'Pass':
                self.apply_poison_dmg()
                print()
                return 'Pass'
            elif decision in self.move_names():
                decision_move = self.get_move(decision)
                if decision_move.mp <= self.mp:
                    if decision_move.hp_cost(self) < self.hp:
                        if controller == 'Player':
                            target = self.choose_target(decision_move, party, other_party)
                        elif controller == 'Easy':
                            target = self.choose_target_easy(decision_move, party, other_party)
                        elif controller == 'Hard':
                            #placeholder
                            target = self.choose_target_easy(decision_move, party, other_party)
                        else:
                            raise ValueError(f"Unrecognized controller: {controller}")
                        if target != 'back':
                            print([demon.name for demon in target])
                            press_turns = self.initiate_move(decision_move, target, other_party, kagutsuchi,
                                                             turn_against_party)
                            # reset charm effect
                            if turn_against_party:
                                other_party.add_demon(self)
                            return press_turns
                    else:
                        if self.hp <= 0:
                            raise RuntimeError('Dead demon encountered in active party.')
                        print('Not enough HP.')
                else:
                    print('Not enough MP.')
            else:
                print('Unrecognized input.\n')

    def unknown_str(self):
        output = f'Demon: {self.race} {self.name}'
        if self.dead:
            output += ' DEAD'
        output += f', Level ???\n\n'
        if self.magatama != 'None':
            output += f'Magatama: ???\n\n'
        output += f'HP: ???/??? MP: ???/???\n\n'
        output += f'Moves: ???\n\n'
        output += f'Passives: ???\n\n'
        output += f'Status: {print_list(self.list_statuses())}\n'
        output += f'Taru: {self.taru_total()} (+{self.taru_plus}/-{self.taru_minus})\n'
        output += f'Maka: {self.maka_total()} (+{self.maka_plus}/-{self.maka_minus})\n'
        output += f'Raku: {self.raku_total()} (+{self.raku_plus}/-{self.raku_minus})\n'
        output += f'Suku: {self.suku_total()} (+{self.suku_plus}/-{self.suku_minus})\n\n'
        output += f'Strength: ???\n'
        output += f'Magic: ???\n'
        output += f'Vitality: ???\n'
        output += f'Agility: ???\n'
        output += f'Luck: ???\n\n'
        output += f'Reflects: ???\n'
        output += f'Absorbs: ???\n'
        output += f'Voids: ???\n'
        output += f'Resists: ???\n'
        output += f'Weaknesses: ???\n\n'
        output += 'Analyze this demon for more information...\n'
        return output

    def __str__(self):
        output = f'Demon: {self.race} {self.name}'
        if self.dead:
            output += ' DEAD'
        output += f', Level {self.level}\n\n'
        if self.magatama != 'None':
            output += f'Magatama: {self.magatama}\n\n'
        output += f'HP: {self.hp}/{self.max_hp} MP: {self.mp}/{self.max_mp}\n\n'
        output += f'Moves: {print_list(self.move_names())}\n\n'
        output += f'Passives: {print_list(self.passive_names())}\n\n'
        output += f'Status: {print_list(self.list_statuses())}\n'
        output += f'Taru: {self.taru_total()} (+{self.taru_plus}/-{self.taru_minus})\n'
        output += f'Maka: {self.maka_total()} (+{self.maka_plus}/-{self.maka_minus})\n'
        output += f'Raku: {self.raku_total()} (+{self.raku_plus}/-{self.raku_minus})\n'
        output += f'Suku: {self.suku_total()} (+{self.suku_plus}/-{self.suku_minus})\n\n'
        output += f'Strength: {self.str}\n'
        output += f'Magic: {self.mag}\n'
        output += f'Vitality: {self.vit}\n'
        output += f'Agility: {self.ag}\n'
        output += f'Luck: {self.luck}\n\n'
        output += f'Reflects: {print_list(self.reflect)}\n'
        output += f'Absorbs: {print_list(self.absorb)}\n'
        output += f'Voids: {print_list(self.void)}\n'
        output += f'Resists: {print_list(self.resist)}\n'
        output += f'Weaknesses: {print_list(self.weak)}\n'
        return output


# In[19]:


class DemiFiend(Demon):
    def __init__(self, name='Demi-Fiend', target_lv='None', party='None'):
        super().__init__(name, target_lv=target_lv)

    def dict_pull_init(self, name, target_lv):
        self.name = 'Demi-Fiend'
        if name == 'Demi-Fiend':
            all_magatamas = list(magatama_dict.keys())
            if target_lv == 'None':
                possible_magatamas = all_magatamas
            else:
                possible_magatamas = []
                for magatama in all_magatamas:
                    if magatama == 'Masakados':
                        magatama_level = 95
                    else:
                        magatama_level = magatama_dict[magatama]['Moves'][-1][1]
                    if magatama_level < target_lv + RANDOM_DEMON_RANGE:
                        if magatama_level > target_lv - RANDOM_DEMON_RANGE:
                            possible_magatamas.append(magatama)
                if len(possible_magatamas) == 0: # possible if target level plus random range < 19 or > 95
                    if 99-target_lv > 50: # small target level
                        possible_magatamas.append('Marogareh')
                        possible_magatamas.append('Ankh')
                    else: # large target level
                        possible_magatamas.append('Masakados')
                        possible_magatamas.append('Kailash')
            name = random.choice(possible_magatamas)
        self.magatama = name
        # skills include all of current magatama; random lower-level skills
        # level
        if name == 'Masakados':
            self.level = 95
        else:
            self.level = magatama_dict[name]['Moves'][-1][1]
        # race
        magatama_levels = [magatama_dict[name]['Moves'][-1][1] for name in list(magatama_dict.keys())]
        magatama_levels = [95 if n == 1 else n for n in magatama_levels]  # masakados adjust
        self.race = 'Fiend'
        if self.level >= 95:
            self.race = 'King'
        elif magatama_dict[name]['Alignment'] == 'Neutral':
            if self.level >= np.quantile(magatama_levels, .8):
                self.race = 'Phenom'
            elif self.level >= np.quantile(magatama_levels, .6):
                self.race = 'Master'
            elif self.level >= np.quantile(magatama_levels, .4):
                self.race = 'Expert'
            elif self.level >= np.quantile(magatama_levels, .2):
                self.race = 'Adept'
        elif magatama_dict[name]['Alignment'] == 'Light':
            if self.level >= np.quantile(magatama_levels, .8):
                self.race = 'Spirit'
            elif self.level >= np.quantile(magatama_levels, .6):
                self.race = 'Saint'
            elif self.level >= np.quantile(magatama_levels, .4):
                self.race = 'Zealot'
            elif self.level >= np.quantile(magatama_levels, .2):
                self.race = 'Votary'
        elif magatama_dict[name]['Alignment'] == 'Dark':
            if self.level >= np.quantile(magatama_levels, .8):
                self.race = 'Lord'
            elif self.level >= np.quantile(magatama_levels, .6):
                self.race = 'Slayer'
            elif self.level >= np.quantile(magatama_levels, .4):
                self.race = 'Battler'
            elif self.level >= np.quantile(magatama_levels, .2):
                self.race = 'Soldier'
        self.attack_changes = {}
        # temp way to learn moves
        moves = except_key(magatama_dict, name, 'Moves', [])
        # remove unimplemented so that df always has 8 moves
        new_moves = []
        for move_tuple in moves:
            if move_tuple[0] in moves_dict or move_tuple[0] in passives_dict:
                new_moves.append(move_tuple)
        moves = new_moves
        # finding all possible moves from other magatama to add
        possible_moves = []
        for magatama, magatama_info in magatama_dict.items():
            if magatama != 'Masakados':
                for move_tuple in magatama_info['Moves']:
                    if move_tuple not in moves:
                        possible_moves.append(move_tuple)
        # add pierce to possibilities
        possible_moves.append(('Pierce', 1))
        random.shuffle(possible_moves)
        while len(moves) < 8 and len(possible_moves) >= 1:
            # level check: makes sure all moves can be learned
            # ex: lv24, can't learn 2 lv23 moves
            level_check = self.level - possible_moves[0][1]
            for move in moves:
                if move[1] >= self.level:
                    level_check -= 1
            if level_check >= 0:
                moves.append(possible_moves[0])
            del possible_moves[0]
        for move in moves:
            if move[0] in moves_dict and move[0] not in self.move_names():
                self.moves.append(Move(move[0]))
            if move[0] in passives_dict and move[0] not in self.passive_names():
                self.passives.append(Passive(move[0]))
        self.moves.append(Move('Summon'))
        # determine stats
        str_mod = magatama_dict[name]['Strength']
        mag_mod = magatama_dict[name]['Magic']
        vit_mod = magatama_dict[name]['Vitality']
        ag_mod = magatama_dict[name]['Agility']
        luck_mod = magatama_dict[name]['Luck']
        self.str = 2 + str_mod
        self.mag = 2 + mag_mod
        self.vit = 2 + vit_mod
        self.ag = 2 + ag_mod
        self.luck = 2 + luck_mod
        total_mod = str_mod + mag_mod + vit_mod + ag_mod + luck_mod
        stats = ['str', 'mag', 'vit', 'ag', 'luck']
        stat_weights = [str_mod, mag_mod, vit_mod, ag_mod, luck_mod]
        stat_weights = [n + 3 for n in stat_weights]
        for i in range(self.level):
            deciding = True
            while deciding:
                stat_choice = random.choices(stats, weights=stat_weights)[0]
                if stat_choice == 'str' and self.str < 40:
                    self.str += 1
                    deciding = False
                elif stat_choice == 'mag' and self.mag < 40:
                    self.mag += 1
                    deciding = False
                elif stat_choice == 'vit' and self.vit < 40:
                    self.vit += 1
                    deciding = False
                elif stat_choice == 'ag' and self.ag < 40:
                    self.ag += 1
                    deciding = False
                elif self.luck < 40:
                    self.luck += 1
                    deciding = False
        # resistances
        self.reflect = set(except_key(magatama_dict, name, 'Reflect', []))
        self.absorb = set(except_key(magatama_dict, name, 'Absorb', []))
        self.void = set(except_key(magatama_dict, name, 'Void', []))
        self.resist = set(except_key(magatama_dict, name, 'Resist', []))
        self.weak = set(except_key(magatama_dict, name, 'Weaknesses', []))
        self.evolution = 'None'
        self.calc_init()


# In[20]:

class Rotation:
    def __init__(self, party):
        self.party = party
        self.order = [[demon, False] for demon in self.party.demons]

    def next(self):
        for demon_info in self.order:
            if not demon_info[1]:
                demon_info[1] = True
                return demon_info[0]
        # go back to top of list
        for demon_info in self.order:
            demon_info[1] = False
        self.order[0][1] = True
        return self.order[0][0]

    def reset(self):
        self.order = [[demon, False] for demon in self.party.demons]

    def update(self):
        new_order = []
        # remove demons not in party
        for demon_info in self.order:
            if demon_info[0] in self.party.demons:
                new_order.append(demon_info)
        # add demons in party but not rotation
        for demon in self.party.demons:
            if demon not in [demon_info[0] for demon_info in new_order]:
                new_order.append([demon, False])
        self.order = new_order
        self.order.sort(key=lambda x: x[0].ag, reverse=True)

    def __str__(self):
        return print_list([demon[0].name for demon in self.order])

class Party:
    def __init__(self, demons):
        self.demons = sorted(demons, key=operator.attrgetter('ag'), reverse=True)  # sorts by agility
        for demon in self.demons:
            demon.party = self
        self.stock = []  # can take in stock demons later
        for demon in self.stock:
            demon.party = self
        self.party_stat_calc()  # defines party lv/ag/luck
        self.rotation = Rotation(self)

    def list_demon_names(self):
        return [demon.name for demon in self.demons]

    def party_stat_calc(self):
        '''used to calculate party-wide stats for selecting random demons (level) and who_goes_first
           (agility+luck). Separate from __init__ to call when adding/removing demons.'''
        level = 0
        ag = 0
        luck = 0
        for demon in self.demons:
            level += demon.level
            ag += demon.ag
            luck += demon.luck
        if len(self.demons) > 0:
            self.level = level / len(self.demons)
            self.ag = ag / len(self.demons)
            self.luck = luck / len(self.demons)
        else:
            self.level = level
            self.ag = ag
            self.luck = luck

    def demifiend_in_party(self):
        df_in_party = False
        for demon in self.demons:
            if demon.magatama != 'None':
                df_in_party = True
        return df_in_party

    def add_demon(self, demon):
        if demon not in self.demons:
            self.demons.append(demon)
            demon.party = self
            self.party_stat_calc()
            self.demons.sort(key=operator.attrgetter('ag'), reverse=True)
            return True
        return False

    def remove_demon(self, demon):
        if demon in self.demons:
            self.demons.remove(demon)
            demon.party = 'None'
            self.party_stat_calc()
            return True
        return False

    def remove_active_demon(self, demon):
        if demon in self.demons:
            self.demons.remove(demon)
            self.party_stat_calc()
            return True
        return False

    def random_targets(self, max_hits):
        targets = []
        target_lists = []
        for demon in self.demons:
            target_lists.append([demon, 0])
        # decide how many hits actually happen
        if len(target_lists) == 1:
            random_target_num = random.randint(1, 2)
        elif max_hits == 4:
            # does this also depend on number of enemies? no data about it
            random_target_num = random.randint(2, 4)
        elif max_hits == 5:
            # formula approximation
            random_target_value = random.randint(1, 100 + (20 * (len(target_lists) - 4)))
            if random_target_value <= 33:
                random_target_num = 3
            elif random_target_value <= 67:
                random_target_num = 4
            else:
                random_target_num = 5
        # decide how many hits go to each demon
        for i in range(random_target_num):
            choosing = True
            break_counter = 0
            while choosing:
                max_target_check = [target_list[1] for target_list in target_lists]
                if 0 not in max_target_check or 1 not in max_target_check:
                    choosing = False
                random_index = random.randint(0, len(target_lists) - 1)
                if target_lists[random_index][1] < 2:
                    target_lists[random_index][1] += 1
                    choosing = False
                break_counter += 1
                if break_counter > 255:
                    print('multi-target break!')
                    break
        for target_list in target_lists:
            for i in range(target_list[1]):
                targets.append(target_list[0])
        return targets

    def summonable_demons(self):
        alive_demons = []
        for demon in self.stock:
            if demon.dead == False:
                alive_demons.append(demon)
        return alive_demons

    def dead_demons(self):
        dead_demon_list = []
        for demon in self.stock:
            if demon.dead:
                dead_demon_list.append(demon)
        return dead_demon_list

    def summon(self, demon):
        if demon in self.stock and demon.dead == False:
            self.stock.remove(demon)
            self.add_demon(demon)
            self.demons.sort(key=operator.attrgetter('ag'), reverse=True)

    def unsummon(self, demon):
        if demon in self.demons:
            self.remove_active_demon(demon)
            self.stock.append(demon)

    def death_update(self):
        for demon in self.demons:
            if demon.dead:
                self.stock.append(demon)

        for demon in self.stock:
            if demon in self.demons:
                self.remove_active_demon(demon)
        self.rotation.update()

    def lose_check(self):
        if len(self) == 0:
            return True
        return False

    def heal(self):
        dead_demons = []
        for demon in self.stock:
            dead_demons.append(demon)
        # necessary to avoid iteration skips
        for demon in dead_demons:
            demon.hp = 1
            demon.dead = False
            self.summon(demon)
        for demon in self.demons:
            demon.heal()

    def __len__(self):
        return len(self.demons)

    def quick_view(self, start_label=1):
        for demon in self.demons:
            output = f'[{self.demons.index(demon) + start_label}] '
            output += f'{demon.name} HP: {demon.hp}/{demon.max_hp} MP: {demon.mp}/{demon.max_mp}'
            if len(demon.statuses) >= 1:
                output += f' Status: {demon.list_statuses()}'
            print(output)

    def __str__(self):
        output = ''
        for demon in self.demons:
            output += f'{demon}\n'
        return output


# In[21]:


class PressTurns:
    def __init__(self, party):
        self.max_turns = len(party)
        self.full_turns = len(party)
        self.half_turns = 0

    def subtract_turns(self, n):
        while n > 0:
            if self.half_turns > 0:
                if self.half_turns >= n:
                    self.half_turns -= n
                    n = 0
                else:
                    n -= self.half_turns
                    self.half_turns = 0
            elif self.full_turns > 0:
                if self.full_turns >= n:
                    self.full_turns -= n
                    n = 0
                else:
                    n -= self.full_turns
                    self.full_turns = 0
            else:
                n = 0

    def subtract_half_turn(self):
        if self.full_turns > 0:
            self.full_turns -= 1
            self.half_turns += 1
        elif self.half_turns > 0:
            self.half_turns -= 1

    def pass_turn(self):
        if self.half_turns > 0:
            self.half_turns -= 1
        elif self.full_turns > 0:
            self.full_turns -= 1
            self.half_turns += 1

    def use_turn(self, turns_used):
        if turns_used == 'All':
            self.subtract_turns(self.max_turns)
        elif turns_used == 'Pass':
            self.pass_turn()
        elif turns_used == 0.5:
            self.subtract_half_turn()
        else:
            self.subtract_turns(turns_used)

    def check_turns(self):
        if self.full_turns == 0 and self.half_turns == 0:
            return False
        return True

    def __str__(self):
        output = []
        for i in range(self.max_turns - (self.full_turns + self.half_turns)):
            output.append('O')
        for i in range(self.half_turns):
            output.append('*')
        for i in range(self.full_turns):
            output.append('X')
        return str(output)


# In[23]:


class FourVsFour:
    # not actually four vs four— changes based on demons inputted
    def __init__(self, kagutsuchi=Kagutsuchi()):
        self.kagutsuchi = kagutsuchi
        self.party1 = Party([])
        self.party2 = Party([])
        self.controllers = ['Player', 'Comp']
        self.ran = False
        self.difficulties = ['Easy']
        self.turns = 0
        self.match_party1_length = False
        self.stopped_game = False

    def select_players(self):
        player_options = ['Player vs. Comp', 'Player vs. Player', 'Comp vs. Comp']
        print(f'The current player options are as follows: {print_list(player_options)}')
        selected_mode = h_input('Select a mode: ', "Player Select")
        if selected_mode != '':  # defaults to pvc (defined in init)
            selected_mode = process.extractOne(selected_mode, player_options)[0]
            if selected_mode == 'Player vs. Player':
                self.controllers[1] = 'Player'
            elif selected_mode == 'Comp vs. Comp':
                self.controllers[0] = 'Comp'
        for i in range(len(self.controllers)):
            if self.controllers[i] == 'Comp':
                if len(self.difficulties) > 1:
                    input_str = 'Select the difficulty of the '
                    if self.controllers.count('Comp') > 1:
                        input_str += ordinal(i + 1)
                    input_str += f'comp ({print_list(self.difficulties)}): '
                    selected_difficulty = h_input(input_str, 'Difficulty')
                    if selected_difficulty == '':
                        # defaults to previous difficulty if choosing for second player (2 comps)
                        if i > 0:
                            if self.controllers[i - 1] in self.difficulties:
                                selected_difficulty = self.controllers[i - 1]
                            # defaults to first otherwise
                            else:
                                selected_difficulty = self.difficulties[0]
                        else:
                            selected_difficulty = random.choice(self.difficulties)
                    else:
                        selected_difficulty = process.extractOne(selected_difficulty, self.difficulties)[0]
                    self.controllers[i] = selected_difficulty
                else:
                    # doesn't ask player if only 1 difficulty implemented
                    self.controllers[i] = self.difficulties[0]

    def create_player_party(self, party, target_lv='None'):
        demons = []
        random_party = False
        demon_count = 4-len(party)
        for i in range(demon_count):
            player_input = h_input(f'Choose the {ordinal(i + 1)} demon in your party: ', 'Choosing a Party').lower()
            if player_input == 'random':
                random_party = True
                break
            elif player_input == '':
                if len(demons) < 1:
                    random_party = True
                else:
                    self.match_party1_length = True
                break
            elif player_input.isnumeric() and 1 <= int(player_input) <= 99:
                target_lv = int(player_input)
                random_party = True
                break
            else:
                player_input = process.extractOne(player_input, master_list)[0]
                player_input, evolve = find_evolve_count(player_input)
                if player_input in demon_dict:
                    demons.append(Demon(player_input, evolutions=evolve))
                else:
                    demons.append(DemiFiend(player_input))
        for demon in demons:
            party.add_demon(demon)
        if random_party:
            self.create_random_party(party, target_lv=target_lv)

    def create_random_party(self, party, target_lv='None'):
        if self.match_party1_length:
            party_length = len(self.party1)
        else:
            party_length = 4
        if len(party) == 0:
            party.add_demon(DemiFiend(target_lv=target_lv, party=party))
        # following if statement is to make sure level selection adheres to parameter instead of current party lv
        if target_lv == 'None': # unspecified target level: uses party level average
            if len(party) < party_length and not party.demifiend_in_party():
                party.add_demon(DemiFiend(target_lv=party.level, party=party))
            while len(party) < party_length:
                party.add_demon(Demon(target_lv=party.level, party=party))
        else: # specified target level
            if len(party) < party_length and not party.demifiend_in_party():
                party.add_demon(DemiFiend(target_lv=target_lv, party=party))
            while len(party) < party_length:
                party.add_demon(Demon(target_lv=target_lv, party=party))

    def who_goes_first(self):
        # normally: base value = 72, capped between 85 and 50
        party1_chance = 50 + self.party1.level + (self.party1.luck / 2) + self.party1.ag
        party1_chance -= self.party2.level + (self.party2.luck / 2) + self.party2.ag
        if random.randint(0, 100) <= party1_chance:
            return 1
        return 2

    def player_turn(self, party, other_party):
        press_turns = PressTurns(party)
        if self.controllers[0] == 'Player' and self.controllers[1] in self.difficulties:
            print('Your turn!\n')
        else:
            if party == self.party1:
                print("Player 1's turn!\n")
            else:
                print("Player 2's turn!\n")
        for demon in party.demons:
            demon.tick_statuses()
        party.rotation.reset()
        while press_turns.check_turns() and self.check_victory() == False:
            print(f'Press turns: {press_turns}   Kagutsuchi: {str(self.kagutsuchi)}')
            print('Demon order:', party.rotation)
            used_turns = party.rotation.next().action(party, other_party, 'Player', self.kagutsuchi)
            if used_turns == 'Stop':
                self.stopped_game = True
                break
            else:
                press_turns.use_turn(used_turns)
                other_party.death_update()
                party.death_update()
        if self.check_victory() or used_turns == 'Stop':
            return True
        print(f'Press turns: {press_turns}\n')
        return False

    def comp_turn(self, party, other_party, difficulty):
        press_turns = PressTurns(party)
        if self.controllers[0] == 'Player' and self.controllers[1] in self.difficulties:
            print('Enemy turn!\n')
        else:
            if party == self.party1:
                print("Player 1's turn!\n")
            else:
                print("Player 2's turn!\n")
        for demon in party.demons:
            demon.tick_statuses()
        party.rotation.reset()
        while press_turns.check_turns() and self.check_victory() == False:
            print(f'Press turns: {press_turns}    Kagutsuchi: {str(self.kagutsuchi)}')
            press_turns.use_turn(party.rotation.next().action(party, other_party, difficulty, self.kagutsuchi))
            other_party.death_update()
            party.death_update()
        if self.check_victory():
            return True
        print(f'Press turns: {press_turns}\n')
        return False

    def turn(self, party, other_party, controller):
        self.turns += 1
        if self.turns > 255:
            print('Turn limit (255) reached!')
            return True
        if controller == 'Player':
            return self.player_turn(party, other_party)
        else:
            return self.comp_turn(party, other_party, controller)

    def check_victory(self):
        if self.party1.lose_check() or self.party2.lose_check():
            return True
        return False

    def run(self):
        if self.ran:
            self.party1.heal()
            self.party2.heal()
            self.turns = 0
            self.stopped_game = False
            self.match_party1_length = False
        else:
            self.select_players()
            if self.controllers[0] == 'Player':
                self.create_player_party(self.party1)
            else:
                self.create_random_party(self.party1)
            if self.controllers[1] == 'Player':
                self.create_player_party(self.party2, target_lv=self.party1.level)
            else:
                self.create_random_party(self.party2, target_lv=self.party1.level)
            self.ran = True
        print(f"party: df: {str([demon.level for demon in self.party1.demons if demon.magatama != 'None'])}")
        print(f"party: df mag: {str([demon.magatama for demon in self.party1.demons if demon.magatama != 'None'])}")
        print(f'party: avg: {self.party1.level}')
        print(f"comp: df: {str([demon.level for demon in self.party2.demons if demon.magatama != 'None'])}")
        print(f"comp: df mag: {str([demon.magatama for demon in self.party2.demons if demon.magatama != 'None'])}")
        print(f'comp: avg: {self.party2.level}')
        current_turn = self.who_goes_first()
        victory = False
        while victory == False:
            if current_turn == 1:
                victory = self.turn(self.party1, self.party2, self.controllers[0])
                current_turn = 2
            elif current_turn == 2:
                victory = self.turn(self.party2, self.party1, self.controllers[1])
                current_turn = 1
        output_dict = {'Kagutsuchi': self.kagutsuchi, 'Stop': self.stopped_game}
        self.kagutsuchi += 1
        if self.party1.lose_check():
            if self.controllers[0] == 'Player' and self.controllers[1] in self.difficulties:
                print('You lost.')
            else:
                print('Player 2 wins!')
            output_dict['Winner'] = 'Player 2'
        elif self.party2.lose_check():
            if self.controllers[0] == 'Player' and self.controllers[1] in self.difficulties:
                print('You won!')
            else:
                print('Player 1 wins!')
            output_dict['Winner'] = 'Player 1'
        else:
            print('Tie!')
            output_dict['Winner'] = 'Tie'
        return output_dict


# In[24]:


class AutoFourVsFour(FourVsFour):
    def __init__(self, info, kagutsuchi=Kagutsuchi()):
        super().__init__(kagutsuchi)
        self.info = info
        for demon in self.info['Demons 1']:
            self.party1.add_demon(demon)
        for demon in self.info['Demons 2']:
            self.party2.add_demon(demon)
        self.party1.heal()
        self.party2.heal()

    def select_players(self):
        if 'Controller 1' in self.info:
            self.controllers[0] = self.info['Controller 1']
        else:
            self.controllers[0] = self.difficulties[0]
        if 'Controller 2' in self.info:
            self.controllers[1] = self.info['Controller 2']
        else:
            self.controllers[1] = self.difficulties[0]

    def create_random_party(self, party, target_lv='None'):
        if party == self.party1 and self.info['Target Level 1'] != 'None':
            super().create_random_party(party, target_lv=self.info['Target Level 1'])
        elif party == self.party2 and self.info['Target Level 2'] != 'None':
            super().create_random_party(party, target_lv=self.info['Target Level 2'])
        else:
            super().create_random_party(party, target_lv=target_lv)


# In[25]:


def experiment(game_modes):
    print('\nEntering experiment mode...\n')
    game_modes.remove('Experiment')
    p1_wins = 0
    p2_wins = 0
    ties = 0
    default_test_info = {
        'Trials': 2500,
        'Game Mode': '4 vs. 4',
        'Same Teams': False,
        'Target Level 1': 75,
        'Target Level 2': 'None',
        'Demons 1': [],
        'Demons 2': [],
        'Kagutsuchi': Kagutsuchi(),
        'Log Games': True,
        'File Name': 'gamelog'
    }
    test_info = copy.deepcopy(default_test_info)
    #setting changing
    settings_names = list(test_info.keys())
    while True:
        settings_display = ''
        for s_name in settings_names:
            if 'Demons' in s_name:
                names = [f'Demi-Fiend ({x.magatama})' if x.magatama != 'None' else x.name for x in test_info[s_name]]
                settings_display += f'{s_name}: {names}\n'
            else:
                settings_display += f'{s_name}: {test_info[s_name]}\n'
        print(f'Settings:\n{settings_display}')
        changing_setting = h_input('Choose a setting to change or press enter: ', 'Settings Overview')
        if changing_setting == '':
            break
        else:
            changing_setting = process.extractOne(changing_setting, settings_names+['Default'])[0]
        if changing_setting == 'Trials':
            valid_input = False
            while not valid_input:
                setting_val = h_input('Enter the number of trials: ', 'Set Trials')
                if setting_val == '':
                    setting_val = default_test_info['Trials']
                    print(f'The number of trials will be set to the default value.')
                    valid_input = True
                elif setting_val.isnumeric():
                    setting_val = int(setting_val)
                    if setting_val >= 1:
                        valid_input = True
                    else:
                        print('The number must be greater than or equal to 1.\n')
                else:
                    print('The input must be numeric.\n')
            print(f'Trial number set to {setting_val}.')
        elif changing_setting == 'Game Mode':
            if len(game_modes) > 1:
                valid_input = False
                while not valid_input:
                    print(f'The current game modes are as follows: {print_list(game_modes)}')
                    setting_val = h_input('Enter a game mode: ', 'Set Game Mode')
                    if setting_val == '':
                        setting_val = default_test_info['Game Modes']
                        print(f'The game mode will be set to the default.')
                        valid_input = True
                    else:
                        setting_val = process.extractOne(setting_val, game_modes)
                        valid_input = True
            else:
                print(f'Only one game mode is available ({game_modes[0]}).')
                setting_val = game_modes[0]
            print(f'Game mode set to {setting_val}.')
        elif changing_setting == 'Same Teams':
            valid_input = False
            while not valid_input:
                setting_val = h_input('Use the same teams every battle? (y/n): ', 'Set Same Teams').lower()
                if setting_val == '':
                    setting_val = default_test_info['Same Teams']
                    print(f'Team carry-over will be set to the default.')
                    valid_input = True
                elif setting_val == 'y' or setting_val == 'yes':
                    setting_val = True
                    valid_input = True
                elif setting_val == 'n' or setting_val == 'no':
                    setting_val = False
                    valid_input = True
                else:
                    print('The input must be "y", "yes", "n", or "no".\n')
            print(f'Teams set to {"carry over" if setting_val else "remake"} after each battle.')
        elif changing_setting == 'Target Level 1':
            valid_input = False
            while not valid_input:
                setting_val = h_input('Enter the target level of party 1: ', 'Set Target Level')
                if setting_val.isnumeric():
                    setting_val = int(setting_val)
                    if 1 <= setting_val <= 99:
                        valid_input = True
                    else:
                        print('The number must be between 1 and 99, inclusive.\n')
                elif setting_val.title() == 'None' or setting_val == '':
                    valid_input = True
                    setting_val = 'None'
                else:
                    print('The input must be numeric or "None".\n')
            print(f'Target level for party 1 set to {setting_val}.')
        elif changing_setting == 'Target Level 2':
            valid_input = False
            while not valid_input:
                setting_val = h_input('Enter the target level of party 2: ', 'Set Target Level')
                if setting_val.isnumeric():
                    setting_val = int(setting_val)
                    if 1 <= setting_val <= 99:
                        valid_input = True
                    else:
                        print('The number must be between 1 and 99, inclusive.\n')
                elif setting_val.title() == 'None' or setting_val == '':
                    valid_input = True
                    setting_val = 'None'
                else:
                    print('The input must be numeric or "None".\n')
            print(f'Target level for party 2 set to {setting_val}.')
        elif changing_setting == 'Demons 1':
            setting_val = []
            while len(setting_val) < 4:
                demon_input = h_input(f'Choose the {ordinal(len(setting_val) + 1)} demon in party 1: ', 'Set Demons')
                if demon_input == '':
                    break
                demon_input = process.extractOne(demon_input, master_list)[0]
                demon_input, evolve = find_evolve_count(demon_input)
                if demon_input in demon_dict:
                    setting_val.append(Demon(demon_input, evolutions=evolve))
                    print(f'{setting_val[-1].name} was added to party 1.')
                else:
                    setting_val.append(DemiFiend(demon_input))
                    print(f'{setting_val[-1].name} ({setting_val[-1].magatama}) was added to party 1.')
            sv_demon_names = [f'Demi-Fiend ({x.magatama})' if x.magatama != 'None' else x.name for x in setting_val]
            print(f'Specified demons in party 1: {print_list(sv_demon_names)}')
        elif changing_setting == 'Demons 2':
            setting_val = []
            while len(setting_val) < 4:
                demon_input = h_input(f'Choose the {ordinal(len(setting_val) + 1)} demon in party 2: ', 'Set Demons')
                if demon_input == '':
                    break
                demon_input = process.extractOne(demon_input, master_list)[0]
                demon_input, evolve = find_evolve_count(demon_input)
                if demon_input in demon_dict:
                    setting_val.append(Demon(demon_input, evolutions=evolve))
                    print(f'{setting_val[-1].name} was added to party 2.')
                else:
                    setting_val.append(DemiFiend(demon_input))
                    print(f'{setting_val[-1].name} ({setting_val[-1].magatama}) was added to party 2.')
            sv_demon_names = [f'Demi-Fiend ({x.magatama})' if x.magatama != 'None' else x.name for x in setting_val]
            print(f'Specified demons in party 2: {print_list(sv_demon_names)}')
        elif changing_setting == 'Kagutsuchi':
            valid_phase_input = False
            while not valid_phase_input:
                setting_kg_phase = h_input('Enter the kagutsuchi phase (0-8): ', 'Set Kagutsuchi')
                if setting_kg_phase.isnumeric():
                    setting_kg_phase = int(setting_kg_phase)
                    if 0 <= setting_kg_phase <= 8:
                        valid_phase_input = True
                    else:
                        print('The number must be between 0 and 8 (inclusive).\n')
                elif setting_kg_phase.title() == 'Dead':
                    valid_phase_input = True
                    setting_kg_phase = 'Dead'
                elif setting_kg_phase.title() == 'Random' or setting_kg_phase == '':
                    valid_phase_input = True
                    setting_kg_phase = 'Random'
                else:
                    print('The input must be numeric, "Dead", or "Random".\n')
            valid_frozen_input = False
            while not valid_frozen_input:
                setting_kg_frozen = h_input('Prevent kagutsuchi phase changes? (y/n): ', 'Set Kagutsuchi').lower()
                if setting_kg_frozen == 'y' or setting_kg_frozen == 'yes':
                    setting_kg_frozen = True
                    valid_frozen_input = True
                elif setting_kg_frozen == 'n' or setting_kg_frozen == 'no' or setting_kg_frozen == '':
                    setting_kg_frozen = False
                    valid_frozen_input = True
                else:
                    print('The input must be "y", "yes", "n", or "no".\n')
            setting_val = Kagutsuchi(setting_kg_phase, setting_kg_frozen)
            print(f'Kagutsuchi set to: {setting_val.more_info()}')
        elif changing_setting == 'Log Games':
            valid_input = False
            while not valid_input:
                setting_val = h_input('Save the game logs to a text file? (y/n): ', 'Set Log Games').lower()
                if setting_val == '':
                    setting_val = default_test_info['Log Games']
                    print(f'Log saving will be set to the default.')
                    valid_input = True
                elif setting_val == 'y' or setting_val == 'yes':
                    setting_val = True
                    valid_input = True
                elif setting_val == 'n' or setting_val == 'no':
                    setting_val = False
                    valid_input = True
                else:
                    print('The input must be "y", "yes", "n", or "no".\n')
            if setting_val:
                print(f'The game logs will be saved to {test_info["File Name"]}.txt.')
            else:
                print('Game output will be displayed in the console.')
        elif changing_setting == 'File Name':
            valid_input = False
            while not valid_input:
                valid_input = True
                setting_val = h_input('Enter the desired log file name: ', 'Set File Name')
                if setting_val == '':
                    setting_val = default_test_info['File Name']
                    print(f'The file name will be set to the default value.')
                else:
                    for char in setting_val:
                        if not char.isalpha() and not char.isnumeric():
                            if char != "_":
                                valid_input = False
                if not valid_input:
                    print('The file name must contain only letters and numbers.\n')
            print(f'The game log file will be called "{setting_val}".txt.')
        if changing_setting == 'Default':
            print('All settings will be restored to the defaults.')
            confirm_reset = h_input('Type "back" to return or anything else to proceed: ', 'Default Settings')
            if confirm_reset != 'back':
                test_info = copy.deepcopy(default_test_info)
                print('Settings reset to default.')
        else:
            test_info[changing_setting] = setting_val
        print()
    #game initiation
    if test_info['Game Mode'] == '4 vs. 4':
        game = AutoFourVsFour(test_info, kagutsuchi=test_info['Kagutsuchi'])
    # redirect standard output to file
    if test_info['Log Games']:
        orig_stdout = sys.stdout
        f = open(f'{test_info["File Name"]}.txt', 'w')
        sys.stdout = f
        start_time = timeit.default_timer()
    # run games
    for i in range(test_info['Trials']):
        game_info = game.run()
        if game_info['Winner'] == 'Player 1':
            p1_wins += 1
        elif game_info['Winner'] == 'Player 2':
            p2_wins += 1
        else:
            ties += 1
        # print update
        if test_info['Log Games']:
            sys.stdout = orig_stdout
            current_time = timeit.default_timer()
            info_str = f'\rGames played: {i+1}/{test_info["Trials"]}'
            info_str += f'\tElapsed time: {round(current_time-start_time, 3)}s'
            print(info_str, end='')
            sys.stdout = f
        # remake game
        if not test_info['Same Teams']:
            if test_info['Game Mode'] == '4 vs. 4':
                game = AutoFourVsFour(test_info, kagutsuchi=test_info['Kagutsuchi'])
            else:
                raise RuntimeError('Missing game mode')
    # close/reset output
    if test_info['Log Games']:
        sys.stdout = orig_stdout
        f.close()
        print()
    summary_str = f'Total score: {p1_wins} to {p2_wins} ('
    if p1_wins > p2_wins:
        summary_str += 'Player 1 leading'
    elif p2_wins > p1_wins:
        summary_str += 'Player 2 leading'
    else:
        summary_str += 'tied'
    if ties > 0:
        summary_str += f', {ties} ties'
    summary_str += ') \n'
    print(summary_str)


# In[26]:


def main():
    game_modes = ['4 vs. 4', 'Experiment']
    playing = True
    runback = False
    p1_wins = 0
    p2_wins = 0
    ties = 0
    kagutsuchi = Kagutsuchi()
    print('Welcome to NocturneTS!\nAt any time, type "help" for commands and rule explanations.\n')
    while playing:
        if runback == False:
            print(f'The current game modes are as follows: {print_list(game_modes)}')
            selected_mode = h_input('Choose a game mode: ', 'Game Modes')
            if selected_mode == '':
                selected_mode = game_modes[0]
            else:
                selected_mode = process.extractOne(selected_mode, game_modes)[0]
            if selected_mode == '4 vs. 4':
                game = FourVsFour(kagutsuchi=kagutsuchi)
            elif selected_mode == 'Experiment':
                experiment(game_modes)
                break
        game_info = game.run()
        if game_info['Winner'] == 'Player 1':
            p1_wins += 1
        elif game_info['Winner'] == 'Player 2':
            p2_wins += 1
        else:
            ties += 1
        summary_str = f'Total score: {p1_wins} to {p2_wins} ('
        if p1_wins > p2_wins:
            summary_str += 'Player 1 leading'
        elif p2_wins > p1_wins:
            summary_str += 'Player 2 leading'
        else:
            summary_str += 'tied'
        if ties > 0:
            summary_str += f', {ties} tie'
            if ties > 1:
                summary_str += 's'
        summary_str += ')'
        print(summary_str)
        if game_info['Stop']:
            playing = False
        else:
            print()
            repeat_decision = h_input('Play again? (y/n) ', 'Game End').lower()
            #could incorporate fuzzywuzzy
            if repeat_decision == 'y' or repeat_decision == 'yes':
                runback_decision = h_input('Same teams? (y/n) ', 'Game End').lower()
                if runback_decision == 'y' or runback_decision == 'yes':
                    runback = True
                else:
                    runback = False
            else:
                playing = False


# In[29]:


if __name__ == "__main__":
    main()


# In[27]:



