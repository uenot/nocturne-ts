from __future__ import annotations
import sys
import timeit
from fuzzywuzzy import process
import random
import copy
import numpy as np
import json
from typing import Optional, Union, Tuple, List

# global utility function
def ordinal(n: int) -> str:
    """
    Returns an ordinal phrase (first, second, etc.) given a number. Not related to ord().

    :param n: Number between 0 and 16 (inclusive)
    :return: Ordinal string
    """
    # could pretty easily add more, just not necessary
    ordinals = ['zeroth', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh',
                'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth', 'thirteenth', 'fourteenth',
                'fifteenth', 'sixteenth']
    if n > len(ordinals) or n < 0:
        raise ValueError('ordinals input number must be between 0 and 16')
    return ordinals[n]


# global variables


with open("database/demons.json", 'r') as f:
    demon_dict = json.load(f)

with open("database/magatama.json", 'r') as f:
    magatama_dict = json.load(f)

with open("database/moves.json", 'r') as f:
    moves_dict = json.load(f)

with open("database/passives.json", 'r') as f:
    passives_dict = json.load(f)

master_list = ['Demi-Fiend'] + list(demon_dict.keys()) + list(magatama_dict.keys())

# sorted by priority
status_list = ['Stone', 'Fly', 'Stun', 'Charm', 'Poison', 'Mute', 'Bind', 'Panic', 'Sleep', 'Freeze', 'Shock']

# plus/minus threshold for random demon level, given a target level
RANDOM_DEMON_RANGE = 12


# program-specific global functions

def find_evolve_count(demon: str) -> Tuple[str, int]:
    """
    Finds the base form of a demon and the number of evolutions to get to its current form. If the given demon
    has no evolutions, returns the demon's name and 0.

    Ex: find_evolve_count('Hanuman') -> ('Onkot', 1)

    :param demon: Name of the demon to get info about
    :return: Base demon name, number of evolutions
    """
    searching_evolutions = True
    evolve = 0
    while searching_evolutions:
        temp_evolve = evolve
        for demon_name in demon_dict:
            if demon_dict[demon_name]['Evolution'] is not None and demon == demon_dict[demon_name]['Evolution'][0]:
                demon = demon_name
                evolve += 1
        if temp_evolve == evolve:
            searching_evolutions = False
    return demon, evolve


def game_help(topic: Optional[str] = None) -> None:
    """
    Opens interactive help menu.
    :param topic: If specified, opens target topic directly instead of opening the main menu.
    """
    viewing = True
    while viewing:
        if not topic:
            main_topics = ['Intro', 'Game Modes', 'Player Select', 'Difficulty', 'Choosing a Party', 'Move Selection']
            main_topics += ['Target Selection', 'Game End']
            program_topics = ['Random Party Selection', 'View Commands', 'Demi-Fiend Creation']
            mechanic_topics = ['Battle Basics', 'Press Turns', 'Resistances', 'Special Effects', 'The Stock']
            mechanic_topics += ['Demi-Fiend', 'Kagutsuchi']
            experiment_topics = ['Settings Overview', 'Set Trials', 'Set Game Mode', 'Set Same Teams']
            experiment_topics += ['Set Target Level', 'Set Demons', 'Set Kagutsuchi Phase', 'Set Kagutsuchi Freeze']
            experiment_topics += ['Set Log Games', 'Set File Name''Default Settings']
            topics = main_topics + program_topics + mechanic_topics + experiment_topics
            if 'back' in topics:
                topics.remove('back')
            help_explain_str = 'For a detailed look at any of the topics below, type "help {topic}". '
            help_explain_str += 'Type "back" to return to the game.\n\n'
            help_explain_str += 'Topics:\n'
            help_explain_str += f'Instructions: {", ".join(main_topics)}\n'
            help_explain_str += f'Game Mechanics: {", ".join(mechanic_topics)}\n'
            help_explain_str += f'Program-Specific Info: {", ".join(program_topics)}\n'
            help_explain_str += f'Settings for Experiment Mode: {", ".join(experiment_topics)}'
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
            output = 'Currently, three game modes exist: "4 vs. 4", "Endurance", and "Experiment". '
            output += 'You can access any of them by typing out their name in the input prompt.\n\n'
            output += '4 vs. 4 is the standard mode, and can be accessed through the selection prompt '
            output += 'by entering nothing, as well as typing out "4 vs. 4". '
            output += 'The name refers to the number of party members on each team, not the number of players '
            output += 'required. This mode uses 2 controllers, which can be any combination of '
            output += 'human players and computers (more info in the "player selection" section).\n\n'
            output += 'Endurance is played similarly to 4 vs. 4, except that the game continues until Player 1 dies. '
            output += "Player 1's goal is to win as many times as possible. Their team will not heal between rounds, "
            output += "whereas Player 2's team will refresh every round.\n\n"
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
            output += 'Type the name of the mode you want to simulate: either 4 vs. 4 or Endurance.'
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
        elif topic == 'Set Kagutsuchi Phase':
            output = 'This allows you to specify the starting Kagutsuchi phase. Type a number between 0 and 8 to '
            output += 'represent the phase, where 0 is new and 8 is full. '
            output += 'You can also specify "dead", which means Kagutsuchi will never have an effect, or "random", '
            output += 'which gives a random phase.\n\n '
            output += 'Note that by default Kagutsuchi will still rotate (see "Set Kagutsuchi Freeze").'
        elif topic == 'Set Kagutsuchi Freeze':
            output = 'This controls whether Kagutsuchi rotates between games or not. To diable rotation, '
            output += 'type "y" or "yes". Otherwise, type "n" or "no".\n\n'
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
        print(output + '\n')
        topic = None


def h_input(message: str = '', topic: Optional[str] = None) -> str:
    """
    Custom extension of the input() function that integrates the game_help() function. If the user enters "help",
    then the game_help menu is opened. Otherwise, input is returned like normal.

    :param message: Prompt to print next to input field
    :param topic: If specified and user inputs "help", opens the topic directly instead of the main help menu.

    :return: The user input.
    """
    user_input = input(message)
    while user_input == 'help':
        print()
        game_help(topic=topic)
        user_input = input(message)
    return user_input


# classes

class Kagutsuchi:
    """
    Limited extension of an int object. Simulates moon phases: cycles between 0 and 8 upon addition.
    """

    # can implement other numeric/comparison functions if needed: not necessary right now
    def __init__(self, phase: Union[int, str] = 'Random', frozen: bool = False) -> None:
        """
        Constructor for the Kagutsuchi class.

        :param phase: The starting phase, between 0 and 8. Can also be "Dead", which nullifies all Kagutsuchi effects
            and prevents rotation, or "Random" (the default), which sets the starting phase randomly.
        :param frozen: If True, stops the phase value from changing.
        """
        # could add direction parameter— wouldn't really serve a purpose in bigger game context?
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

    def __add__(self, n: int) -> Kagutsuchi:
        """
        Overriding the add method, allowing for addition using the + symbol.

        :param n: The number of phases to pass through.
        :return: Self (the Kagutsuchi object being operated on).
        """
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

    def __eq__(self, n: int) -> bool:
        """
        Overriding the equals method, allowing for equality checks using ==.

        :param n: The phase number to compare to.
        :return: True if the n matches the current phase, False otherwise.
        """
        if self.phase == n and not self.dead:
            return True
        return False

    def __str__(self) -> str:
        """
        Gets a short description of the object based on the current phase.

        :return: Phrase describing the Kagutsuchi phase.
        """
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


class Move:
    """
    Represents the move of a demon. Attributes mainly contain info about the move, and methods provide interfaces
    for using and modifying the move.
    """

    def __init__(self, name: str) -> None:
        """
        Constructor for Move. Sets attributes based on the info in moves_dict.

        :param name: The name of the move to create.
        """
        self.name = name
        # deepcopying because adding specials affects base moves_dict otherwise
        move_info = copy.deepcopy(moves_dict[name])
        self.target = move_info['Target']
        self.category = move_info['Category']
        self.dmg_calc = move_info['Damage Calc']  # distinguishes between HP-based and level-based phys moves
        self.element = move_info['Element']
        self.hits = move_info['Hits']
        self.power = move_info['Power']
        # correction, limit, and peak are hidden values for magic moves used in damage calculation
        self.correction = move_info['Correction']
        self.limit = move_info['Limit']
        if self.power is not None and self.correction is not None and self.limit is not None:
            self.peak = round(((self.limit - self.correction) / self.power) * (255 / 24))
        else:
            self.peak = None
        self.accuracy = move_info['Accuracy']
        self.mp = move_info['MP']
        self.hp = move_info['HP']
        self.specials = move_info['Special Effects']
        self.crit = move_info['Crit']
        self.pierce = False
        self.reset()

    def reset(self) -> None:
        """
        Sets the temporary attributes for the move. Called within __init__. Separate in order to reset the attributes
        after using the move.
        """
        self.reflected = False
        self.temp_dmg_factor = 1

    def create_special(self, effect_info: dict = {}) -> dict:
        """
        Takes in effect_info dict; updates it to defaults. Used when creating new special effects, usually
        through passives (such as Dright/Dark Might and drain attack).

        :param effect_info: The desired non-default parameters for the info for an effect.
        :return: The effect_info dict updated with default values.
        """
        effect_info.setdefault('Element', self.element)
        effect_info.setdefault('Accuracy', 100)
        effect_info.setdefault('Value', 0)
        effect_info.setdefault('Target', 'Same')
        effect_info.setdefault('Condition', None)
        return effect_info

    def update(self, changes: dict = {}) -> None:
        """
        Updates the move based on parameters specified in info_dict. Also sets properties that result from
        attribute changes, such as the Shatter special effect. Used primarily for updating based on
        a demon's attack changes.

        :param changes: Dictionary with parameters to change as keys and the new values as values.
        """
        # could add more changes, but not necessary
        # could incorporate other move edits (such as the changes made by passives)
        for change_type, new_value in changes.items():
            if change_type == 'Element':
                self.element = new_value
            elif change_type == 'Hits':
                self.hits = new_value
                self.power = int(self.power / new_value)

        # set "shatter" effect based on element
        if self.element == 'Phys':
            self.specials['Shatter'] = self.create_special({'Accuracy': 50, 'Condition': 'Target Stone'})
        elif self.element == 'Force':
            self.specials['Shatter'] = self.create_special({'Accuracy': 75, 'Condition': 'Target Stone'})
        else:
            del self.specials['Shatter']

    def hp_cost(self, user: Demon) -> int:
        """
        Calculates the absolute HP cost of a move for a given demon.

        :param user: The demon using the move.
        :return: The HP cost for the demon.
        """
        return int(self.hp * user.max_hp / 100)

    def user_cost_string(self, user: Demon) -> str:
        """
        Creates a string which displays the cost of a move for a given demon.

        :param user: The demon using the move.
        :return: Info about the cost of the move.
        """
        if self.mp != 0:
            return f'{self.mp} MP'
        elif self.hp != 0:
            return f'{self.hp_cost(user)} HP'
        else:
            return 'None'

    def calculate_element_effect(self, target: Demon) -> Tuple[str, str, str]:
        """
        Calculates the elemental effect of the move on a demon. More extensive than Demon.find_element_effect;
        considers barriers and frozen status. Non-destructive.

        :param target: The demon to calculate the move's effect on.
        :return: The effect ('Reflect', 'Void', etc.), the overriding barrier effect, and the barrier name.
            If no barrier is hit, the second and third items will be None.
        """
        ''''''
        barrier_effect = None
        barrier = None
        element_effect = target.find_element_effect(self.element)
        if self.reflected:
            if element_effect == 'Reflect' or element_effect == 'Absorb':
                element_effect = 'Void'
        # check for temp barriers
        if self.element != 'Almighty' and self.element is not None:
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
                element_effect = None
            elif element_effect == 'Weak/Resist':
                element_effect = 'Weak'
        return element_effect, barrier_effect, barrier

    def calculate_accuracy(self, user: Demon, target: Demon) -> float:
        """
        Calculates the hit chance of the move given a user demon and a target demon. Separate from calculate_hit
        because the accuracy value is used in calculate_crit.

        :param user: The demon using the move.
        :param target: The demon being targeted with the move.
        :return: The chance for the move to hit as a number between 0 and 100.
        """
        if 'Shock' in target.list_statuses() or 'Freeze' in target.list_statuses():
            hit_chance = 100
        elif self.accuracy is None:
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

    def calculate_hit(self, user: Demon, target: Demon) -> float:
        """
        Decides if the move hits given a user demon and a target demon.

        :param user: The demon using the move.
        :param target: The demon being targeted with the move.
        :return: True if the move hits and False otherwise.
        """
        return self.calculate_accuracy(user, target) < random.randint(1, 100)

    def calculate_base_damage(self, user: Demon, target: Demon, power_factor: float = 1) -> float:
        """
        Calculates the base damage of the move given a user demon and a target demon. Does not take into account
        the random damage multiplier and any temporary modifiers (represented by self.temp_dmg_factor).

        :param user: The demon using the move.
        :param target: The demon being targeted with the move.
        :param power_factor: A multiplier for the effective move power. Can affect move damage differently than
            multiplying the result. Used exclusively with MP draining.
        :return: The base damage for the move.
        """
        if self.power is not None:
            power = self.power * power_factor
            if self.dmg_calc == 'Mag':
                if user.level <= self.peak:
                    damage = 0.004 * (5 * (user.mag + 36) - user.level)
                    # since a value is added to the multiple of power here, the result differs when
                    # multiplying base power versus multiplying the function result
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
                damage = None
        # if the move heals but has no power, will heal to full
        elif 'Heal' in self.specials:
            damage = target.max_hp - target.hp
        else:
            damage = None
        # buff/debuff modifiers
        if damage is not None:
            if self.category == 'Physical':
                damage *= user.taru_mod()
            elif self.category == 'Magic':
                damage *= user.maka_mod()
            if 'Heal' not in self.specials:
                damage /= target.raku_mod()
        return damage

    def calculate_crit(self, user: Demon, target: Demon, kagutsuchi: Kagutsuchi = Kagutsuchi('Dead')) -> bool:
        """
        Decides if the move is a critical hit given a user demon and a target demon.

        :param user: The demon using the move.
        :param target: The demon being targeted with the move.
        :param kagutsuchi: The current Kagutsuchi. Affects Bright/Dark Might. If not specified, assumes no effect.
        :return: True if the move crits and False otherwise.
        """
        crit_proc = False
        if self.crit is not None:
            if 'Shock' in target.list_statuses() or 'Freeze' in target.list_statuses():
                crit_chance = 100
            elif 'Bright Might' in self.specials and kagutsuchi == 8:
                crit_chance = 100
            elif 'Dark Might' in self.specials and kagutsuchi == 0:
                crit_chance = 100
            else:
                if self.accuracy is None:
                    base_accuracy = 100
                else:
                    base_accuracy = self.accuracy
                crit_chance = self.crit * self.calculate_accuracy(user, target) / base_accuracy
            if crit_chance >= random.randint(1, 100):
                crit_proc = True
        return crit_proc

    def unknown_str(self) -> str:
        """
        Modified __str__ method that obscures significant info. Called when the user has no information
        about a demon that posesses this move.

        :return: A string formatted like __str__, but with question marks.
        """
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

    def __str__(self) -> str:
        """
        Overrides string representation of a Move. Displays all relevant info about the move. Notably omits
        complex damage calculation stats.

        :return: String containing information about the object.
        """
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
        if self.power is not None:
            output += f'Base Power: {self.power}\n'
        if self.accuracy is not None:
            output += f'Base Accuracy: {self.accuracy}\n'
        if self.crit is not None:
            output += f'Base Crit Chance: {self.crit}\n'
        for effect, effect_info in self.specials.items():
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
            if effect_info['Condition'] is not None:
                output += f'Condition: {effect_info["Condition"]}, '
            if effect_info['Target'] != 'Same':
                output += f'Target: {effect_info["Target"]}, '
            if effect_info['Element'] != self.element:
                output += f'Element: {effect_info["Element"]}, '
            output += f'{effect_info["Accuracy"]}% chance)\n'
        return output


class PassiveAbility:
    """
    Represents an ability of a passive. Contains the actual effects of the passive. Separate from the Passive class
    because a Passive can contain multiple passive abilities. None of the methods are meant to be called outside
    of methods in the Passive class; as Passive acts as a wrapper around the PassiveAbility methods.
    """

    def __init__(self, effect: str, element: Optional[str], value: Optional[float]) -> None:
        """
        Constructor for the PassiveAbility object.

        :param effect: The effect of the passive ability.
        :param element: The element of the passive ability. Used for resistances and boosts. Can be None if the chosen
            effect doesn't require an element.
        :param value: A number to apply to a move/demon parameter. Actual usage varies based on the chosen effect.
            Can be None if the chosen element doesn't require a value.
        """
        self.effect = effect
        self.element = element
        self.value = value

    def init_apply(self, demon: Demon) -> None:
        """
        Applies the effect of the passive ability. Called when a demon is initialized.

        :param demon: The demon to apply the passive effect to.
        """
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
            if demon.get_move('Attack').crit is not None:
                demon.get_move('Attack').crit *= self.value
        elif self.effect == 'Bright Might':
            demon.get_move('Attack').specials['Bright Might'] = demon.get_move('Attack').create_special()
        elif self.effect == 'Dark Might':
            demon.get_move('Attack').specials['Dark Might'] = demon.get_move('Attack').create_special()
        elif self.effect == 'Drain':
            special = demon.get_move('Attack').create_special({'Value': self.value})
            demon.get_move('Attack').specials['HP Drain'] = special
        elif self.effect == 'Attack All':
            demon.get_move('Attack').target = 'All Enemies'
        elif self.effect == 'Pierce':
            for move in demon.moves:
                if move.category == 'Physical':
                    move.pierce = True

    def attack_apply(self, move: Move) -> None:
        """
        Applies the effect of the passive ability. Called when a demon attacks with a given move.

        :param move: The move to apply the passive effect to.
        """
        if self.effect == 'Boost':
            if self.element == move.element and self.element is not None:
                move.temp_dmg_factor *= 1.5
            # boost effect with no element boosts all moves
            elif self.element is None and move.element is not None:
                move.temp_dmg_factor *= 1.5

    def counter_apply(self, user: Demon, target: Demon, kagutsuchi: Kagutsuchi = Kagutsuchi('Dead')) -> bool:
        """
        Initiates counter-attacks. Called when a counter-attack is meant to be initiated. Checks for if the
        effect of the ability is "Counter".

        :param user: The demon who was attacked and is countering.
        :param target: The attacking demon to be counter-attacked.
        :param kagutsuchi: The current Kagutsuchi phase. Defaults to "Dead" if not specified.
        :return: True if a counter-attack was initiated, False otherwise.
        """
        if self.effect == 'Counter':
            print(f'\n{user.name} countered!')
            user.get_move('Attack').temp_dmg_factor *= self.value
            # reflected shares same properties as counters— can't be reflected back or trigger further counters
            user.get_move('Attack').reflected = True
            user.initiate_move(user.get_move('Attack'), [target], target.party, kagutsuchi)
            return True
        return False

    def __str__(self) -> str:
        """
        String representation of a PassiveAbility.

        :return: Information about the passive ability.
        """
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
            if boost_element is None:
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


class Passive:
    """
    Represents a passive. Acts essentially as a wrapper around a list of PassiveAbility objects, with most methods
    calling the associated PassiveAbility method for each object in the self.abilities list.
    """

    def __init__(self, name: str) -> None:
        """
        Constructor for the Passive object. Sets attributes based on the info in passives_dict.

        :param name: The name of the passive to be created.
        """
        self.name = name
        # creates PassiveAbility for each info set in passives_dict
        self.abilities = []
        for ability in passives_dict[name]:
            self.abilities.append(PassiveAbility(ability['Effect'], ability['Element'], ability['Value']))

    def init_apply(self, demon: Demon) -> None:
        """
        Applies the effect of the passive. Called when a demon is initialized.

        :param demon: The demon to apply the passive to.
        """
        for ability in self.abilities:
            ability.init_apply(demon)

    def attack_apply(self, move: Move) -> None:
        """
        Applies the effect of the passive. Called when a demon attacks with a given move.

        :param move: The move to apply the passive effect to.
        """
        for ability in self.abilities:
            ability.attack_apply(move)

    def counter_apply(self, user: Demon, target: Demon, kagutsuchi: Kagutsuchi = Kagutsuchi('Dead')) -> bool:
        """
        Initiates counter-attacks. Called when a counter-attack is meant to be initiated. Checks for if the
        effect of the ability is "Counter".

        :param user: The demon who was attacked and is countering.
        :param target: The attacking demon to be counter-attacked.
        :param kagutsuchi: The current Kagutsuchi phase. Defaults to "Dead" if not specified.
        :return: True if a counter-attack was initiated, False otherwise.
        """
        for ability in self.abilities:
            # ensures that only one counter is triggered
            # this catches multiple counter PassiveAbilities— multiple counter Passives must be caught elsewhere
            # would occur as the result of a strange entry in passives_dict
            if ability.counter_apply(user, target, kagutsuchi):
                return True
        return False

    def unknown_str(self) -> str:
        """
        Modified __str__ method that obscures significant info. Called when the user has no information
        about a demon that posesses this passive.

        :return: A string formatted like __str__, but with question marks.
        """
        return f'Passive: {self.name}\nEffect: ???'

    def __str__(self) -> str:
        """
        Overrides string representation of a Passive. Lists the PassiveEffects associated with the passive.

        :return: String containing information about the object.
        """
        output = f'Passive: {self.name}\nEffect'
        ability_strings = []
        for ability in self.abilities:
            ability_strings.append(str(ability))
        if len(ability_strings) >= 2:
            output += 's'
        output += f': {", ".join(ability_strings)}'
        return output


class Status:
    """
    Represents a status ailment. Main purpose is to figure out when the ailment should be healed naturally through
    tick(). Effects of statuses are applied via "in" checks with the demon's list of statuses.
    """

    def __init__(self, name: str) -> None:
        """
        Constructor for the Status class.

        :param name: The name of the status to be created.
        """
        self.name = name
        self.timer = 0
        if self.name == 'Freeze' or self.name == 'Shock':
            self.max_time = 1
        elif self.name in ['Charm', 'Bind', 'Panic', 'Sleep']:
            self.max_time = 4
        else:
            self.max_time = None

    def tick(self, demon: Demon) -> bool:
        """
        Checks to see if the status has expired. Rolls randomly and checks against the max time.

        :param demon: The demon who possesses the status.
        :return: True if the status expires, False otherwise.
        """
        self.timer += 1
        if self.max_time is not None:
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

    def __str__(self) -> str:
        """
        String representation of a Status. Gives info on what the status does. Currently unused method.

        :return: Description of the status effect.
        """
        output = f'{self.name}: '
        if self.name == 'Stone':
            output += 'Cannot act and can be shattered by physical or force skills.'
        elif self.name == 'Stun':
            output += 'Drastically reduces hit chance of physical moves.'
        elif self.name == 'Charm':
            output += 'Will sometimes turn against the party.'
        elif self.name == 'Poison':
            output += 'Loses 1/8 of max HP every turn and weakens physical moves.'
        elif self.name == 'Mute':
            output += 'Cannot use magic skills.'
        elif self.name == 'Bind':
            output += 'Cannot act.'
        elif self.name == 'Panic':
            output += 'Will sometimes skip actions, and can rarely retreat from battle.'
        elif self.name == 'Sleep':
            output += 'Cannot act. Will slowly regain HP/MP.'
        elif self.name == 'Freeze':
            output += 'Always receives critical hits and loses physical resistance.'
        elif self.name == 'Shock':
            output += 'Always receives critical hits.'
        else:
            output += 'Missing status description.'
        return output


class Demon:
    """
    Represents a demon. Attributes hold distinguishing information about the demon and temporary changes,
    and methods allow for demon-demon interaction as well as standard information retrieval and interfacing.
    """

    def __init__(self, name: Optional[str] = None, evolutions: int = 0, target_lv: Optional[int] = None,
                 party: Optional[Party] = None) -> None:
        """
        Constructor for the Demon class.

        :param name: The name of the demon. If specified, creates the named demon. If not specified, creates
            a random demon.
        :param evolutions: The number of evolutions to undergo at the end of initialization. When creating demons
            that have older forms, this parameter is used to carry over attributes such as moves.
        :param target_lv: The target level of the demon. Relevant only if name is not specified and thus a demon
            will be chosen randomly. If name is not specified and target_lv is, the level of the randomly created
            demon will be close to the target level.
        :param party: The party to which the demon belongs.
        """
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
            if self.evolution is not None:
                self.dict_pull_init(self.evolution[0])
                self.reset()

    def soft_reset(self) -> None:
        """
        Resets most temporary attributes. Separate from reset() in order to be called during endurance battles.
        """
        new_statuses = []
        # carries over some statuses
        for status in self.statuses:
            if status.name in ['Stone', 'Stun', 'Poison', 'Mute']:
                new_statuses.append(status)
        self.statuses = new_statuses
        # resets all other misc. stuff
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

    def reset(self) -> None:
        """
        Resets temporary attributes. Called during __init__ to define those attributes. Separate from __init__
        in order to be called elsewhere, such as in heal().
        """
        self.dead = False
        self.statuses = []
        self.soft_reset()

    def dict_pull_init(self, name: Optional[str] = None, target_lv: Optional[int] = None) -> None:
        """
        Subset of __init__ method; separate in order to call multiple times during evolution and to override in
        subclasses. Sets all "info" attributes, such as name, stats, moves, etc. based on demon_dict.

        :param name: The name of the demon. If not specified, chooses a random demon to create.
        :param target_lv: The target level of a randomly generated demon. Only used if name is not specified.
        """
        # random selection
        if name is None:
            possible_members = copy.deepcopy(list(demon_dict.keys()))
            random.shuffle(possible_members)
            for member in possible_members:
                # check for if demon is already in party
                party_check = True
                if self.party is not None:
                    if member in self.party.list_demon_names():
                        party_check = False
                if party_check:
                    # check if level falls within target_lv range (if specified)
                    level_cap = False
                    if target_lv is not None:
                        if demon_dict[member]['Level'] > target_lv + RANDOM_DEMON_RANGE:
                            level_cap = True
                        elif demon_dict[member]['Level'] < target_lv - RANDOM_DEMON_RANGE:
                            level_cap = True
                    if not level_cap:
                        name, self.evo_num = find_evolve_count(member)
                        break
        # define attributes
        self.name = name
        self.race = demon_dict[name]['Race']
        self.attack_changes = demon_dict[name]['Attack']
        base_moves = demon_dict[name]['Base Moves']
        for move in base_moves:
            if move in moves_dict and move not in self.move_names():
                self.moves.append(Move(move))
            if move in passives_dict and move not in self.passive_names():
                self.passives.append(Passive(move))
        # temp way to learn moves
        learned_moves = demon_dict[name]['Learned Moves']
        for move in learned_moves:
            if move[0] in moves_dict and move[0] not in self.move_names():
                self.moves.append(Move(move[0]))
            if move[0] in passives_dict and move[0] not in self.passive_names():
                self.passives.append(Passive(move[0]))
        # shrink move pool to 8 by removing random moves
        if len(self.moves) + len(self.passives) - 1 > 8:  # -1 counts for attack
            removable_moves = []
            # prioritizes removing moves from past evolutions if possible
            for move in self.moves:
                if move.name not in base_moves and move.name not in [x[0] for x in learned_moves]:
                    removable_moves.append(move)
            for passive in self.passives:
                if passive.name not in base_moves and passive.name not in [x[0] for x in learned_moves]:
                    removable_moves.append(passive)
            removable_moves.remove(self.get_move('Attack'))  # can't delete Attack
            random.shuffle(removable_moves)
            while len(self.moves) + len(self.passives) - 1 > 8:
                # case where base demon has more than 8 moves: considers all remaining moves
                if len(removable_moves) == 0:
                    removable_moves = self.moves + self.passives
                    removable_moves.remove(self.get_move('Attack'))
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
        self.reflect = set(demon_dict[name]['Reflect'])
        self.absorb = set(demon_dict[name]['Absorb'])
        self.void = set(demon_dict[name]['Void'])
        self.resist = set(demon_dict[name]['Resist'])
        self.weak = set(demon_dict[name]['Weaknesses'])
        self.evolution = demon_dict[name]['Evolution']
        self.magatama = None
        self.calc_init()

    def calc_init(self) -> None:
        """
        Subset of dict_pull_init. Sets various attributes that are not defined explicitly in dict_pull_init.
        Separate in order to avoid repetition when defining dict_pull_init in subclasses.

        """
        # hp/mp
        self.hp = (self.level + self.vit) * 6
        if self.hp > 999:
            self.hp = 999
        self.max_hp = self.hp
        self.mp = (self.level + self.mag) * 3
        if self.mp > 999:
            self.mp = 999
        self.max_mp = self.mp
        # apply passive abilities
        for passive in self.passives:
            passive.init_apply(self)
        # update attack move
        for move in self.moves:
            if move.name == 'Attack':
                move.update(self.attack_changes)

    def heal(self) -> None:
        """
        Fully heals and resets the demon. Used when resetting games; not intended for use during games.
        """
        self.reset()
        self.hp = self.max_hp
        self.mp = self.max_mp

    def level_up(self) -> None:
        """
        Increases the level of the demon and adjust stats to match. Currently unused.
        """
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
            raised_stat = None
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
        if self.evolution is not None:
            if self.level >= self.evolution[1]:
                print(f'{self.name} is evolving!')
                old_name = self.name
                # could put confirmation in here later, but rn that would suck to do each time
                self.dict_pull_init(self.evolution[0])
                print(f'{old_name} evolved into {self.name}!')

    def hp_percent(self) -> float:
        """
        Gets the percent HP remaining of the demon.

        :return: Current HP divided by max HP.
        """
        return self.hp / self.max_hp

    def get_move(self, move_name: str) -> Optional[Move]:
        """
        Given a move's name, gets the move object belonging to the demon.

        :param move_name: The name of the move to get.
        :return: The Move object with the given name. If multiple Moves have the given name, only one
        will be returned. Returns None if no Moves match the given name.
        """
        for move in self.moves:
            if move.name == move_name:
                return move
        return None

    def move_names(self) -> List[str]:
        """
        Gets a list of the demon's move names.

        :return: A list of strings containing the names of the demon's moves.
        """
        return [move.name for move in self.moves]

    def passive_names(self) -> List[str]:
        """
        Gets a list of the demon's passive names.

        :return: A list of strings containing the names of the demon's passives.
        """
        return [passive.name for passive in self.passives]

    def list_statuses(self) -> List[str]:
        """
        Gets a list of the demon's statuses.

        :return: A list of strings containing the names of the demon's statuses.
        """
        status_strings = []
        for status in self.statuses:
            status_strings.append(status.name)
        return status_strings

    def can_counter(self) -> bool:
        """
        Checks if the demon has the ability to counter.

        :return: True if the demon can counter, False otherwise.
        """
        # cannot counter if died to the attack
        if self.dead:
            return False
        # these statuses immobilize/prevent from countering
        for status in self.list_statuses():
            if status in ['Stone', 'Stun', 'Charm', 'Bind', 'Sleep', 'Freeze', 'Shock']:
                return False
        return True

    def check_status_priority(self, status_name: str) -> bool:
        """
        Checks if the status with the given name is higher priority than any other existing statuses (and can
        therefore be applied).

        :param status_name: The name of the status to check.
        :return: True if the given status is highest priority, False otherwise.
        """
        for status in self.statuses:
            if status_list.index(status_name) > status_list.index(status.name):
                return False
        return True

    def find_element_effect(self, element: str) -> str:
        """
        Finds the base elemental effect on a demon given an element. Called as a part of Move.calculate_element_effect.
        Separate for use in status calculation (which differs from normal moves).

        :param element: The name of the element to check for.
        :return: The effect of the move. Can be 'Reflect', 'Absorb', 'Void', 'Weak/Resist', 'Weak', 'Resist', or
            'Normal'.
        """
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

    def taru_total(self) -> int:
        """
        Finds the total Taru effect on the demon.

        :return: The stages of buff/debuff, between -4 and 4 inclusive.
        """
        return self.taru_plus - self.taru_minus

    def taru_mod(self) -> float:
        """
        Finds the modifier based on Taru buffs/debuffs, to be applied to attack power.

        :return: A power multiplier for physical moves.
        """
        if self.taru_total() >= 0:
            return 1 + (0.25 * self.taru_total())
        else:
            return 1 + (0.125 * self.taru_total())

    def maka_total(self) -> int:
        """
        Finds the total Maka effect on the demon.

        :return: The stages of buff/debuff, between -4 and 4 inclusive.
        """
        return self.maka_plus - self.maka_minus

    def maka_mod(self) -> float:
        """
        Finds the modifier based on Maka buffs/debuffs, to be applied to magic power.

        :return: A power multiplier for magic moves.
        """
        if self.maka_total() >= 0:
            return 1 + (0.25 * self.maka_total())
        else:
            return 1 + (0.125 * self.maka_total())

    def raku_total(self) -> int:
        """
        Finds the total Raku effect on the demon.

        :return: The stages of buff/debuff, between -4 and 4 inclusive.
        """
        return self.raku_plus - self.raku_minus

    def raku_mod(self) -> float:
        """
        Finds the modifier based on Raku buffs/debuffs, to be applied to defense.

        :return: A multiplier for defense.
        """
        if self.raku_total() >= 0:
            return 1 + (0.25 * self.raku_total())
        else:
            return 1 + (0.125 * self.raku_total())

    def suku_total(self) -> int:
        """
        Finds the total Suku effect on the demon.

        :return: The stages of buff/debuff, between -4 and 4 inclusive.
        """
        return self.suku_plus - self.suku_minus

    def suku_mod(self) -> float:
        """
        Finds the modifier based on Suku buffs/debuffs, to be applied to agility.

        :return: A multiplier for accuracy and agility.
        """
        if self.suku_total() >= 0:
            return 1 + (0.25 * self.suku_total())
        else:
            return 1 + (0.125 * self.suku_total())

    def recover_hp(self, n: int) -> int:
        """
        Setter for the HP attribute, to be used in-game. Ensures that HP does not exceed max HP.

        :param n: The amount of HP to be recovered.
        :return: The real amount of HP recovered.
        """
        n = round(n)
        if self.hp + n > self.max_hp:
            recovered_hp = self.max_hp - self.hp
            self.hp = self.max_hp
        else:
            self.hp += n
            recovered_hp = n
        return recovered_hp

    def recover_mp(self, n: int) -> int:
        """
        Setter for the MP attribute, to be used in-game. Ensures that MP does not exceed max MP.

        :param n: The amount of MP to be recovered.
        :return: The real amount of MP recovered.
        """
        if self.mp + n > self.max_mp:
            recovered_mp = self.max_mp - self.mp
            self.mp = self.max_mp
        else:
            self.mp += n
            recovered_mp = n
        return recovered_mp

    def check_max(self) -> None:
        """
        Ensures that HP and MP do not exceed the maximums. If they do, sets them to the maximums.
        """
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        if self.hp < 0:
            self.hp = 0
        if self.mp > self.max_mp:
            self.mp = self.max_mp
        if self.mp < 0:
            self.mp = 0

    def check_max_stats(self) -> bool:
        """
        Ensures that stats do not exceed the maximums. If they do, sets them to the maximums. Currently unused
        (intended to work with level_up).

        :return: True if no stats were adjusted, False otherwise.
        """
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

    def check_dead(self) -> None:
        """
        Checks if the demon is dead and sets the dead attribute. Also checks for endure.
        """
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

    def check_max_buffs(self) -> bool:
        """
        Ensures that buffs/debuffs do not exceed their maximums. If they do, sets them to the max.

        :return: True if no buffs were adjusted, False otherwise.
        """
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

    def effect_tarukaja(self) -> bool:
        """
        Intializes the Tarukaja effect, increasing attack.

        :return: True if the increase actually took effect (not at the maximum), False otherwise.
        """
        self.taru_plus += 1
        return self.check_max_buffs()

    def effect_makakaja(self) -> bool:
        """
        Intializes the Makakaja effect, increasing magic.

        :return: True if the increase actually took effect (not at the maximum), False otherwise.
        """
        self.maka_plus += 1
        return self.check_max_buffs()

    def effect_rakukaja(self) -> bool:
        """
        Intializes the Rakukaja effect, increasing defense.

        :return: True if the increase actually took effect (not at the maximum), False otherwise.
        """
        self.raku_plus += 1
        return self.check_max_buffs()

    def effect_sukukaja(self) -> bool:
        """
        Intializes the Sukukaja effect, increasing agility.

        :return: True if the increase actually took effect (not at the maximum), False otherwise.
        """
        self.suku_plus += 1
        return self.check_max_buffs()

    def effect_tarunda(self) -> bool:
        """
        Intializes the Tarunda effect, decreasing attack and magic.

        :return: True if the decrease actually took effect (not at the minimum), False otherwise.
        """
        # has to check if either taru_minus or maka_minus changed
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

    def effect_rakunda(self) -> bool:
        """
        Intializes the Rakunda effect, decreasing defense.

        :return: True if the decrease actually took effect (not at the minimum), False otherwise.
        """
        self.raku_minus += 1
        return self.check_max_buffs()

    def effect_sukunda(self) -> bool:
        """
        Intializes the Sukunda effect, decreasing agility.

        :return: True if the decrease actually took effect (not at the minimum), False otherwise.
        """
        self.suku_minus += 1
        return self.check_max_buffs()

    def clear_status(self, status_name: str) -> bool:
        """
        Cures a single specified status.

        :param status_name: The name of the status to remove.
        :return: True if the status was found and removed, False otherwise.
        """
        for status in self.statuses:
            if status.name == status_name:
                self.statuses.remove(status)
                return True
        return False

    def clear_statuses(self) -> None:
        """
        Clears all statuses besides Freeze and Shock. For use when applying new statuses.
        """
        for status_name in status_list:
            if status_name != 'Freeze' and status_name != 'Shock':
                self.clear_status(status_name)

    def tick_statuses(self) -> None:
        """
        Updates all temporary attributes, for use at the beginning of a turn. Clears barriers and statuses when
        appropriate.
        """
        self.tetrakarn = False
        self.makarakarn = False
        for status in self.statuses:
            if status.tick(self):
                print(f'{self.name} recovered from {status.name}!\n')
                self.statuses.remove(status)

    def apply_poison_dmg(self) -> None:
        """
        Checks if the demon is poisoned, and if it is, applies poison damage.
        """
        if 'Poison' in self.list_statuses():
            poison_dmg = round(self.max_hp / 8)
            if poison_dmg >= self.hp:
                poison_dmg = self.hp - 1
            self.hp -= poison_dmg
            if poison_dmg > 0:
                print(f'\n{self.name} took {poison_dmg} poison damage!')

    def mute_options(self, options: List[str]) -> List[str]:
        """
        Filters a list of move names, removing magic moves. Updates the given list in place, returns the removed moves.

        :param options: A list of move names.
        :return: A list of the removed move names.
        """
        removed_moves = []
        if 'Mute' in self.list_statuses():
            for option in options:
                if option in moves_dict:
                    if moves_dict[option]['Category'] == 'Magic':
                        removed_moves.append(option)
        for removed_move in removed_moves:
            options.remove(removed_move)
        return removed_moves

    def charmed_options(self, options: List[str]) -> List[str]:
        """
        Filters a list of move names, removing those that cannot be used while charmed. Updates the given list
        in place, returns the removed moves.

        :param options: A list of move names.
        :return: A list of the removed move names.
        """
        # necessary so that charmed demons can't interact with the stock
        removed_moves = []
        for option in options:
            if option in moves_dict:
                if 'Stock' in moves_dict[option]['Target'] or 'Dead' in moves_dict[option]['Target']:
                    removed_moves.append(option)
        for removed_move in removed_moves:
            options.remove(removed_move)
        return removed_moves

    def effect_conditions(self, condition: Optional[str] = None) -> bool:
        """
        Checks if a given condition is met. Used when triggering special effects.

        :param condition: The condition to check. If None, returns True.
        :return: True if the condition is met, False otherwise.
        """
        if condition is None:
            return True
        elif condition == 'Target Asleep':
            if 'Sleep' in self.list_statuses():
                return True
        elif condition == 'Target Poisoned':
            if 'Poison' in self.list_statuses():
                return True
        elif condition == 'Target Stone':
            if 'Stone' in self.list_statuses():
                return True
        return False

    def proc_effect(self, effect: str, value: Optional[float] = None) -> bool:
        """
        Applies a given effect to the demon.

        :param effect: The effect to apply.
        :param value: A number value associated with the effect, used when calculating results.
            Usage varies based on effect.
        :return: True if the effect triggered successfully, False otherwise.
        """
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
            print(f'{self.name} was revived with {int(self.hp)} health!')
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
            else:
                return False
        elif effect == 'Shock':
            if 'Shock' not in self.list_statuses() and 'Freeze' not in self.list_statuses():
                self.statuses.append(Status('Shock'))
                print(f'{self.name} was shocked!')
            else:
                return False
        elif effect == 'Charm':
            if self.check_status_priority('Charm'):
                self.clear_statuses()
                self.statuses.append(Status('Charm'))
                print(f'{self.name} was charmed!')
            else:
                return False
        elif effect == 'Stun':
            if self.check_status_priority('Stun'):
                self.clear_statuses()
                self.statuses.append(Status('Stun'))
                print(f'{self.name} was stunned!')
            else:
                return False
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
            else:
                return False
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
            else:
                return False
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
            else:
                return False
        elif effect == 'Panic':
            if self.check_status_priority('Panic'):
                self.clear_statuses()
                self.statuses.append(Status('Panic'))
                print(f'{self.name} was panicked!')
            else:
                return False
        elif effect == 'Sleep':
            if self.check_status_priority('Sleep'):
                self.clear_statuses()
                self.statuses.append(Status('Sleep'))
                print(f'{self.name} was put to sleep!')
            else:
                return False
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
            else:
                return False
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
            raise RuntimeError(f'Missing move special effect: {effect}.')
        return True

    def choose_target(self, decision_move: Move, party: Party, other_party: Party) -> Union[List[Demon], str]:
        """
        Allows the player to choose a target for a given move through input. If the targets are predefined,
        gives a confirmation prompt.

        :param decision_move: The move to choose targets for.
        :param party: The demon's party.
        :param other_party: The opposing party.
        :return: A list of targets for the move. If 'back' was inputted, returns the string 'back'.
        """
        valid_decision = False
        break_counter = 0
        # while loop catches bad input
        while not valid_decision:
            # single-enemy target
            if decision_move.target == 'Single Enemy':
                print(f'{decision_move.name} will target a single enemy.')
                if len(other_party) >= 1:
                    print(other_party.view_targets())
                    target_decision = h_input('Choose a target number or type "back": ', 'Target Selection').lower()
                    print()
                    if target_decision == 'back':
                        return 'back'
                    else:
                        try:
                            target_decision = int(target_decision)
                            # check if tag with input exists
                            if 1 <= target_decision <= len(other_party):
                                target_list = []
                                # targeted once for each hit in the move
                                for i in range(decision_move.hits):
                                    # input uses 1-indexing; adjusted here
                                    target_list.append(other_party.demons[target_decision - 1])
                                return target_list
                        # catch non-integer input
                        except ValueError:
                            pass
                else:
                    # can occur if the only demon in a party is charmed and switches sides
                    print('There are no valid targets.\n')
                    return 'back'
                print('Invalid input. Please try again.')
            # all-enemy target
            elif decision_move.target == 'All Enemies':
                print(f'{decision_move.name} will target all enemies.')
                # opportunity to return to move selection
                input_str = 'Type "back" to return or type anything else to continue: '
                target_decision = h_input(input_str, 'Target Selection').lower()
                print()
                if target_decision == 'back':
                    return 'back'
                else:
                    target_list = []
                    for demon in other_party.demons:
                        # added once for each hit
                        for i in range(decision_move.hits):
                            target_list.append(demon)
                    return target_list
            # self-target
            elif decision_move.target == 'Self':
                print(f'{decision_move.name} will target {self.name}.')
                input_str = 'Type "back" to return or type anything else to continue: '
                target_decision = h_input(input_str, 'Target Selection').lower()
                print()
                if target_decision == 'back':
                    return 'back'
                else:
                    # multihit loop really shouldn't be necessary here, added just in case
                    # really, it should only matter for single-enemy and all-enemies
                    target_list = []
                    for i in range(decision_move.hits):
                        target_list.append(self)
                    return target_list
            # single-ally target
            elif decision_move.target == 'Single Ally':
                # same as single enemy, but uses party instead of other_party
                print(f'{decision_move.name} will target a single ally.')
                if len(party) >= 1:
                    print(party.view_targets())
                    target_decision = h_input('Choose a target number or type "back": ', 'Target Selection').lower()
                    print()
                    if target_decision == 'back':
                        return 'back'
                    else:
                        try:
                            target_decision = int(target_decision)
                            if 1 <= target_decision <= len(party):
                                target_list = []
                                for i in range(decision_move.hits):
                                    target_list.append(party.demons[target_decision - 1])
                                return target_list
                        # catch non-integer input
                        except ValueError:
                            pass
                else:
                    print('There are no valid targets.\n')
                    return 'back'
                print('Invalid input. Please try again.')
            # all allies except self
            elif decision_move.target == 'Other Allies':
                print(f'{decision_move.name} will target all other allies.')
                input_str = 'Type "back" to return or type anything else to continue: '
                target_decision = h_input(input_str, 'Target Selection').lower()
                print()
                if target_decision == 'back':
                    return 'back'
                else:
                    target_list = []
                    for demon in party.demons:
                        if demon != self:
                            for i in range(decision_move.hits):
                                target_list.append(demon)
                    return target_list
            # all allies (including self)
            elif decision_move.target == 'All Allies':
                print(f'{decision_move.name} will target all allies.')
                input_str = 'Type "back" to return or type anything else to continue: '
                target_decision = h_input(input_str, 'Target Selection').lower()
                print()
                if target_decision == 'back':
                    return 'back'
                else:
                    target_list = []
                    for demon in party.demons:
                        for i in range(decision_move.hits):
                            target_list.append(demon)
                    return target_list
            # random enemies
            elif decision_move.target == "Random Enemies":
                print(f'{decision_move.name} will target random enemies.')
                input_str = 'Type "back" to return or type anything else to continue: '
                target_decision = h_input(input_str, 'Target Selection').lower()
                print()
                if target_decision == 'back':
                    return 'back'
                else:
                    # chooses randomly via this method
                    return other_party.random_targets(decision_move.hits)
            # dead allies
            elif decision_move.target == 'Dead Ally':
                print(f'{decision_move.name} will target a dead demon in your stock.')
                # using .dead_demons() instead of .demons to get the dead demons in stock
                if len(party.dead_demons()) >= 1:
                    print(party.view_dead_targets())
                    target_decision = h_input('Choose a target number or type "back": ', 'Target Selection').lower()
                    print()
                    if target_decision == 'back':
                        return 'back'
                    else:
                        try:
                            target_decision = int(target_decision)
                            if 1 <= target_decision <= len(party.dead_demons()):
                                # not going to implement multihit loop
                                # I can't imagine a scenario where that could possibly be useful
                                # the only things that targets dead demons are revives, where multihits make no sense
                                return [party.dead_demons()[target_decision - 1]]
                        except ValueError:
                            pass
                else:
                    print('There are no valid targets.\n')
                    return 'back'
                print('Invalid input. Please try again.')
            # allies in the stock (but not dead)
            elif decision_move.target == 'Stock Ally':
                print(f'{decision_move.name} will target a demon in your stock.')
                # using .summonable_demons() instead of .demons to get the alive demons in stock
                if len(party.summonable_demons()) >= 1:
                    print(party.view_stock_targets())
                    target_decision = h_input('Choose a target number or type "back": ', 'Target Selection').lower()
                    print()
                    if target_decision == 'back':
                        return 'back'
                    else:
                        try:
                            target_decision = int(target_decision)
                            if 1 <= target_decision <= len(party.summonable_demons()):
                                # same thing here: not bothering with multihit loop
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
                        # same thing here: not bothering with multihit loop
                        return [random.choice(party.summonable_demons())]
                else:
                    print('There are no valid targets.\n')
                    return 'back'
            elif decision_move.target == 'Lowest HP':
                all_demons = party.demons + other_party.demons
                random.shuffle(all_demons)
                all_demons.sort(key=lambda x: x.hp_percent())
                output = f'{decision_move.name} will target the demon with the lowest %HP. '
                output += f'Currently, this is {all_demons[0].name}.'
                print(output)
                input_str = 'Type "back" to return or type anything else to continue: '
                target_decision = h_input(input_str, 'Target Selection').lower()
                print()
                if target_decision == 'back':
                    return 'back'
                else:
                    target_list = []
                    for i in range(decision_move.hits):
                        target_list.append(all_demons[0])
                    return target_list

            # break counter is more of a failsafe than something that's expected to happen
            # especially for player input
            break_counter += 1
            if break_counter >= 255:
                print('Unable to select target.')
                return 'back'

    def use_move(self, move: Move, target: Demon, kagutsuchi: Kagutsuchi = Kagutsuchi('Dead'),
                 input_hit: Optional[bool] = None, input_crit: Optional[bool] = None) -> dict:
        """
        When called, the demon uses the given move on another target demon. Updates demons in place based
        on the move effects.

        :param move: The move to be used.
        :param target: The demon being targeted with the move.
        :param kagutsuchi: The current Kagutsuchi phase. Affects Bright/Dark Might. If not specified, assumes
            no effect.
        :param input_hit: If True, the move is guaranteed to hit; if False, the move will miss. If not specified,
            will calculate hit chance independently.
        :param input_crit: If True, the move is guaranteed to crit; if False, the move will not crit. If not specified,
            will calculate crit chance independently.
        :return: Dictionary containing the press turns used, if the move can be countered, whether the move hit,
            and whether the move crit.
        """
        press_turns = 1  # Tracks the press turns used by the move; default 1
        counter_possible = False  # Tracks whether the move can be countered or not
        move_hit = True  # Tracks whether the move hit
        move_crit = False  # Tracks whether the move crit
        might_crit = False  # Tracks whether the crit was obtained via the Might passive
        # find temp dmg factor
        # check passives for boosts; theoretically other passives that apply on attack trigger here too
        for passive in self.passives:
            passive.attack_apply(move)
        # change power based on statuses
        if 'Stone' in target.list_statuses() and move.element in ['Fire', 'Ice', 'Elec']:
            move.temp_dmg_factor *= 1 / 10
        if 'Poison' in self.list_statuses() and move.category == 'Physical':
            move.temp_dmg_factor *= 1 / 2
        # apply focus
        if self.focus and move.category == 'Physical':
            move.temp_dmg_factor *= 2.5
            self.focus = False
        # check for dodge
        # input_hit can be True, False, or None, so the logic here is a little weird
        # if True, bypasses check; if False, automatically dodges; if None, calls calculate_hit
        if not input_hit:
            if input_hit is not None or move.calculate_hit(self, target):
                move_hit = False
                print(f'{target.name} dodged the attack!')
                press_turns = 2
        # proceed if move connected
        if move_hit:
            # set resistances/weaknesses
            element_effect, barrier_effect, barrier = move.calculate_element_effect(target)
            # remove any consumed barriers
            if barrier == 'Tetrakarn':
                target.tetrakarn = False
            elif barrier == 'Makarakarn':
                target.makarakarn = False
            elif barrier == 'Tetraja':
                target.tetraja = False
            # apply reflection
            if element_effect == 'Reflect' or barrier_effect == 'Reflect':
                if barrier_effect == 'Reflect':
                    print(f"{target.name}'s shield reflected the attack!")
                else:
                    print(f'{target.name} reflected the attack!')
                # reflected attribute makes it so that reflected moves can't be re-reflected or countered
                move.reflected = True
                # uses the move on itself
                # avoids infinite recusion since it cannot be re-reflected
                reflect_move_info = self.use_move(move, self, kagutsuchi, input_hit, input_crit)
                if reflect_move_info['Crit']:
                    move_crit = True
                press_turns = 'All'
            else:
                # calculating for damaging moves + heals
                if move.power is not None or 'Heal' in move.specials:
                    damage = move.calculate_base_damage(self, target)
                    damage *= random.randint(1000, 1100) / 1000  # random variance
                    damage *= move.temp_dmg_factor  # apply the temporary factor (default 1)
                    # calculate crit
                    # more weird logic b/c of True/False/None
                    # if False, bypasses check; if True, auto-crits; if None, calls calculate_crit
                    if input_crit or input_crit is None and move.calculate_crit(self, target, kagutsuchi):
                        move_crit = True
                        # print message based on passives (if they caused the crit)
                        if move.name == 'Attack':
                            if 'Bright Might' in self.passive_names() and kagutsuchi == 8:
                                print(f"{self.name}'s Bright Might activated!")
                            elif 'Dark Might' in self.passive_names() and kagutsuchi == 0:
                                print(f"{self.name}'s Dark Might activated!")
                            elif 'Might' in self.passive_names():
                                print(f"{self.name}'s Might activated!")
                                might_crit = True  # used because drain attack doesn't trigger on Might crits
                        print('Critical hit!')
                        # crit effects: extra damage and half-turn
                        damage *= 3 / 2
                        press_turns = 0.5
                    # elemental effect
                    element_coefficient = 1
                    # in order of priority (excluding reflect, which is triggered earlier)
                    if barrier_effect == 'Void':
                        # pierce shouldn't normally occur here; only expel/death have a void barrier
                        # custom moves could change that theoretically
                        if move.pierce:
                            print('Pierced!')
                        else:
                            element_coefficient = 0
                            print(f"{target.name}'s shield voided the attack!")
                            press_turns = 2
                    elif element_effect == 'Absorb':
                        # in each block: check for pierce
                        if move.pierce:
                            print('Pierced!')
                        else:
                            # adjust element coefficient (multiplying damage by this)
                            element_coefficient = -1
                            print(f'{target.name} absorbed the attack!')
                            # if necessary, adjust press turns
                            press_turns = 'All'
                    elif element_effect == 'Void':
                        if move.pierce:
                            print('Pierced!')
                        else:
                            element_coefficient = 0
                            print(f'{target.name} voided the attack!')
                            press_turns = 2
                    elif element_effect == 'Weak':
                        # no pierce check since this is not a resistance
                        element_coefficient = 1.5
                        print(f'{target.name} was weak to the attack!')
                        press_turns = 0.5
                    elif element_effect == 'Weak/Resist':
                        # weak and resist can apply simultaneously; represented by "Weak/Resist"
                        # prints weakness message; gives half-turn; opportunity to pierce resistance
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
                    # apply element coefficient to damage and round
                    damage = round(damage * element_coefficient)
                    # heal will give HP instead of taking it away
                    if 'Heal' in move.specials:
                        damage *= -1
                    deal_regular_damage = True
                    # MP drain effect
                    if 'MP Drain' in move.specials:
                        # recalculates MP damage based on unique factor
                        power_factor = move.specials['MP Drain']['Value']
                        mp_damage = move.calculate_base_damage(self, target, power_factor)
                        mp_damage *= random.randint(1000, 1100) / 1000
                        mp_damage = round(mp_damage * move.temp_dmg_factor * element_coefficient)
                        # clamp values
                        if mp_damage < 0:
                            mp_damage = 0
                        if target.mp < mp_damage:
                            mp_damage = target.mp
                        # apply changes
                        self.mp += mp_damage
                        target.mp -= mp_damage
                        print(f'{self.name} drained {mp_damage} MP!')
                        print(f'{target.name} lost {mp_damage} MP!')
                        # MP moves only continue to deal_regular_damage if also draining HP
                        # prevents damage from being applied normally if only draining MP
                        # works for all in-game moves, but moves that drain MP and deal damage wouldn't work
                        # TODO: reimplement this to make it more flexible
                        if 'HP Drain' not in move.specials:
                            deal_regular_damage = False
                    if deal_regular_damage:
                        # clamped damage: used for HP drain
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
                            # check if counter could occur (initialize at end of initiate move)
                            if move.category == 'Physical' and not move.reflected:
                                counter_possible = True
                        # print different messages if gained HP
                        elif damage < 0:
                            print(f'{target.name} gained {-damage} health!')
                        elif damage == 0:
                            if 'Heal' in move.specials:
                                print(f"{target.name}'s health is full.")
                            else:
                                print(f'{target.name} took no damage!')
                        # apply HP drain effect
                        if 'HP Drain' in move.specials:
                            hp_damage = round(real_damage_dealt * move.specials['HP Drain']['Value'])
                            if hp_damage < 0:
                                hp_damage = 0
                            # does not trigger if the move critted and Might activated
                            # in the original game, i guess it was something to do with how multiple effects applied
                            # artificially recreating that with this check
                            if not might_crit:
                                self.hp += hp_damage
                                if hp_damage > 0:
                                    print(f'{self.name} drained {hp_damage} HP!')
                                self.check_max()
                else:
                    damage = None
                # special effects
                # TODO: improve flexibility of this section
                # should be sufficient for all existing moves
                # would be wrong if there were two effects with different elements
                # tetraja_status_shield assumes all effects are the same element
                if len(move.specials) > 0:
                    parent_null = False
                    one_proc = False
                    # if the base move was absorbed or voided, the effect will not apply
                    if damage is not None:
                        if element_effect == 'Absorb' or element_effect == 'Void':
                            parent_null = True
                    if not parent_null:
                        tetraja_status_shield = False
                        # iterates through each effect in the move, applying them individually
                        for effect, effect_info in copy.deepcopy(move.specials).items():
                            # target can differ from the target of the original move
                            # the "self" target is handled in initiate move
                            if effect_info['Target'] == 'Same':
                                chance_factor = 1
                                effect_weak = False
                                # find the element of the effect (as opposed to the parent move)
                                temp_element_effect = target.find_element_effect(effect_info['Element'])
                                # apply elemental effects to chance_factor
                                if barrier_effect == 'Void':
                                    # occurs when the parent move hits a barrier in damage calculation
                                    # target.tetraja won't be true but the effect should still be voided
                                    chance_factor *= 0
                                    # tetraja_status_shield detects that a barrier voided the effect
                                    tetraja_status_shield = True
                                elif target.tetraja:
                                    # occurs if the barrier wasn't hit by the normal move's element
                                    if effect_info['Element'] == 'Expel' or effect_info['Element'] == 'Death':
                                        chance_factor *= 0
                                        tetraja_status_shield = True
                                elif temp_element_effect == 'Reflect' or temp_element_effect == 'Absorb':
                                    # reflect can happen if parent move element differs from effect
                                    # can't reflect or absorb effects; just voided
                                    chance_factor *= 0
                                    # if the move has no damage, sets press_turns and prints message
                                    if damage is None:
                                        press_turns = 'All'
                                        print(f'{target.name} voided the attack!')
                                elif temp_element_effect == 'Void':
                                    chance_factor *= 0
                                    if damage is None:
                                        # press turns used differ from reflect/absorb
                                        press_turns = 2
                                        print(f'{target.name} voided the attack!')
                                elif temp_element_effect == 'Weak':
                                    chance_factor *= 1.5
                                    effect_weak = True  # for press turns and print statement
                                    # done separately because the effect has to connect first
                                elif temp_element_effect == 'Weak/Resist':
                                    chance_factor *= 0.75
                                    effect_weak = True
                                elif temp_element_effect == 'Resist':
                                    chance_factor *= 0.5
                                # demi-fiends get extra evasion against insta-kill expel/death attacks
                                if target.magatama is not None:
                                    if effect == 'Kill':
                                        if effect_info['Element'] == 'Expel' or effect_info['Element'] == 'Death':
                                            chance_factor *= 0.5
                                effect_chance = effect_info['Accuracy']
                                # cannot proc these effects: initialized elsewhere separately
                                if effect != 'Heal' and 'Drain' not in effect and 'Might' not in effect:
                                    # effect chance of 100 means that the effect will always hit unless voided
                                    # if effect chance is 100 and the effect is not voided, will bypass chance_factor
                                    if effect_chance < 100 or chance_factor == 0:
                                        effect_chance *= chance_factor
                                    # check against random number
                                    if effect_chance >= random.randint(1, 100):
                                        # check if any conditions are satisfied
                                        if target.effect_conditions(effect_info['Condition']):
                                            # set press turns for weaknesses
                                            if effect_weak and not one_proc and move.power is None:
                                                # TODO: rearrange this
                                                # could print this and still miss in proc_effect
                                                print(f'{target.name} was weak to the attack!')
                                                press_turns = 0.5
                                            # proc_effect applies the effect to the demon
                                            # returns False if the effect didn't work: ex. no status to cure
                                            effect_miss = not target.proc_effect(effect, effect_info['Value'])
                                            one_proc = True  # avoids repeat prints for weaknesses
                                        else:
                                            effect_miss = True
                                    else:
                                        effect_miss = True
                                    # checks if the effect missed and was not voided for print statement
                                    if effect_miss and move.power is None and effect_chance != 0:
                                        if not tetraja_status_shield:
                                            print(f'The effect missed {target.name}!')
                        # get rid of barrier
                        # done here so that it applies to all effects
                        if tetraja_status_shield:
                            print(f"{target.name}'s shield voided the effects!")
                            target.tetraja = False
                # ensures no overflow
                target.check_max()
                self.check_max()
                if not move.reflected:  # doesn't trigger if original user dies to a reflection
                    target.check_dead()
                    if target.dead:
                        print(f'{target.name} died!')
        move.reset()  # resets temp attributes
        return {'Press Turns': press_turns, 'Counter': counter_possible, 'Hit': move_hit, 'Crit': move_crit}

    def initiate_move(self, move: Move, target: List[Demon], other_party: Party = None,
                      kagutsuchi: Kagutsuchi = Kagutsuchi('Dead'), charmed: bool = False) -> Union[str, float]:
        """
        Allows for the demon to use the given move. More extensive than use_move; includes multihits, counters, and
        different-targeting effects.

        :param move: The move to be used.
        :param target: An ordered list of demons to be targeted with the move.
        :param other_party: The opposing party. Used for redirecting multihit moves with random targeting. If not
            specified, will not redirect missing multihits.
        :param kagutsuchi: The current Kagutsuchi phase. Affects Bright/Dark Might. If not specified, assumes
            no effect.
        :param charmed: Default is False. True if the demon has switched sides via charm. If true, prevents
            counters from triggering.
        :return: The press turns used by the move.
        """
        # apply costs
        self.mp -= move.mp
        self.hp -= move.hp_cost(self)
        press_turns = []
        possible_counters = []
        moves_initiated = 0
        move_hit = None
        move_crit = None
        # iterate through demons in target list
        for demon in target:
            # disregard if the demon is dead (possibly from earlier appearances in the target list)
            # exception for moves intended to target dead demons
            if not demon.dead or 'Dead' in move.target:
                print()
                moves_initiated += 1
                # call use_move
                move_outputs = self.use_move(move, demon, kagutsuchi, move_hit, move_crit)
                # add press turns from that call to a list, to be parsed later
                press_turns.append(move_outputs['Press Turns'])
                # if a counter is possible, add the attacked demon to a list of demons that can counter
                if move_outputs['Counter']:
                    possible_counters.append(demon)
                # for standardizing single-target multi-hit accuracy/crit
                if move.hits > 1:
                    if move.target == 'Single Enemy' or move.target == 'All Enemies':
                        # compares the number of times the demon has been targeted vs the expected number
                        if target[:moves_initiated].count(demon) < move.hits:
                            # ensures that following attacks in the multi-hit chain will hit/crit the same
                            move_hit = move_outputs['Hit']
                            move_crit = move_outputs['Crit']
                        else:
                            # resets the hit/crit chances if multi-hit is finished
                            move_hit = None
                            move_crit = None
            # redirect random multihits to other demons if original target died
            elif move.target == 'Random Enemies' and other_party is not None:
                new_targets = []
                for new_demon in other_party.demons:
                    # targets per demon can't exceed 2 for a random-targeting move
                    if not new_demon.dead and target.count(new_demon) < 2:
                        new_targets.append(new_demon)
                if len(new_targets) >= 1:
                    print()
                    # run move, same as above
                    new_target = random.choice(new_targets)
                    move_outputs = self.use_move(move, new_target, kagutsuchi)
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
                    # don't really care about outputs
                    self.use_move(temp_move, self)
                elif effect == 'MP Recover':
                    temp_move = Move('Chakra Drop')
                    temp_move.specials['MP Recover']['Value'] = effect_info['Value']
                    self.use_move(temp_move, self)
                elif effect == 'Kill':
                    self.hp = 0
                else:
                    raise ValueError(f'Effect missing: {effect}')

        # check if user died (to reflects or self-kill effect)
        self.check_dead()
        if not self.dead and not charmed:
            # initialize counters here
            # needed b/c only one per demon, after original move has finished
            for demon in set(possible_counters):
                if self.dead:
                    break
                elif demon.can_counter():
                    # iterates through all passives, only those with counter effects will do anything
                    for passive in demon.passives:
                        # always a 50% chance to trigger
                        if random.randint(0, 1) == 1:
                            # only proceed to break if counter was actually executed
                            if passive.counter_apply(demon, self, kagutsuchi):
                                self.check_dead()
                                break  # necessary to stop multiple counters from triggering

            # also trigger poison damage
            # poison can't kill, so check dead isn't necessary
            if not self.dead:
                self.apply_poison_dmg()
        if self.dead:
            print(f'{self.name} died!')
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
        elif len(press_turns) == 0:
            return 1
        else:
            raise RuntimeError(f'No valid press turn values in the list: {press_turns}.')

    def choose_target_easy(self, decision_move: Move, party: Party, other_party: Party) -> Union[List[Demon], str]:
        """
        Chooses random targets for a move. Similar to choose_target, but takes no player input.

        :param decision_move: The move to select targets for.
        :param party: The user's party.
        :param other_party: The opposing party.
        :return: A list of targets for the move. Only returns 'back' if no valid targets for the move can be found.
        """
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
            all_demons.sort(key=lambda x: x.hp_percent())
            return [all_demons[0]]
        else:
            # happens when targeting method is unimplemented
            print('Unable to select target.')
            return 'back'

    def choose_move_easy(self, party: Party, other_party: Party, charmed: bool = False) -> str:
        """
        Randomly selects a move to use. Ensures that the move is valid and usable.

        :param party: The demon's party.
        :param other_party: The opposing party.
        :param charmed: True if the demon is charmed, False otherwise. Runs charmed_options if true.
        :return: The name of the move to use. If all moves have no valid targets, returns "Pass".
        """
        possible_moves = self.move_names()
        # mute effect
        self.mute_options(possible_moves)
        # charm effect
        if charmed:
            self.charmed_options(possible_moves)
        valid_move = False
        while not valid_move:
            try:
                # choose randomly from list of possible moves
                decision = possible_moves.pop(random.randint(0, len(possible_moves) - 1))
            except ValueError:  # occurs when list is empty
                return 'Pass'
            decision_move = self.get_move(decision)
            # check cost
            if decision_move.mp <= self.mp and decision_move.hp_cost(self) < self.hp:
                # check if valid targets exist
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

    def choose_move_hard(self, party: Party, other_party: Party) -> str:
        """
        Not yet implemented. Once done, will select a move strategically.

        :param party: The demon's party.
        :param other_party: The opposing party.
        :return:
        """
        return self.choose_move_easy(party, other_party)

    def action(self, party: Party, other_party: Party, controller: str,
               kagutsuchi: Kagutsuchi = Kagutsuchi('Dead')) -> Union[str, float]:
        """
        When called, the demon takes an action. Selects and uses a move. Can rely on user input. Some external
        effects are applied here, such as statuses that prevent actions.

        :param party:
        :param other_party:
        :param controller:
        :param kagutsuchi:
        :return:
        """
        valid_decision = False
        while not valid_decision:
            print(f'Current demon: {self.name} HP: {self.hp}/{self.max_hp} MP: {self.mp}/{self.max_mp}')
            turn_against_party = False  # for charm effect: needs to be global variable to check after action ends
            # stone effect
            if 'Stone' in self.list_statuses():
                print(f'\n{self.name} is petrified...')
                return 1
            # charm effect
            elif 'Charm' in self.list_statuses():
                charm_test_party = copy.deepcopy(party)
                charm_test_party.demons.pop()
                # 50% chance to trigger
                # also checks if the demon has an usable move once switching sides
                if random.randint(0, 1) == 1 and self.choose_move_easy(other_party, charm_test_party, True) != 'Pass':
                    print(f'\n{self.name} turned against the party!')
                    turn_against_party = True
                    party, other_party = other_party, party
                    other_party.remove_demon(self)
                    controller = 'Easy'  # signal to choose random move
                else:
                    print(f'\n{self.name} is acting strangely...\n')
                    return 1
            # bind effect
            elif 'Bind' in self.list_statuses():
                print(f'\n{self.name} is bound!\n')
                return 1
            # panic effect
            elif 'Panic' in self.list_statuses():
                # normally 4 possible actions
                panic_actions = 4
                if self.magatama is not None:
                    # demi-fiend can't retreat
                    panic_actions = 3
                random_panic_action = random.randint(1, panic_actions)
                print(f'\n{self.name} is panicked...')
                # 1: normal action
                if random_panic_action == 2:
                    # 2 and 3 are both functionally the same (unless macca and conversations get added)
                    print(f'\n{self.name} dropped some Macca!')
                    return 1
                elif random_panic_action == 3:
                    print(f'\n{self.name} started babbling to {random.choice(other_party.demons).name}!')
                    return 1
                elif random_panic_action == 4:
                    print(f'\n{self.name} retreated!\n')
                    party.unsummon(self)
                    return 1
            # sleep effect
            elif 'Sleep' in self.list_statuses():
                print(f'\n{self.name} is asleep...')
                recovered_hp = self.recover_hp(round(self.max_hp / 8))
                if recovered_hp > 0:
                    print(f'{self.name} recovered {recovered_hp} HP.')
                recovered_mp = self.recover_mp(round(self.max_mp / 8))
                if recovered_mp > 0:
                    print(f'{self.name} recovered {recovered_mp} MP.')
                print()
                return 1
            # player chooses action to take
            if controller == 'Player':
                options = ['Pass', 'View', 'Stop']
                options += self.move_names()
                # mute effect
                muted_moves = self.mute_options(options)
                if len(muted_moves) >= 1:
                    print(f"{self.name} is unable to cast spells!")
                # "view" possibilities: all demons and moves
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
                # only prints moves and "pass"
                move_list_string = 'Your options: '
                for move in self.moves:
                    if move.name not in muted_moves:
                        move_list_string += f'{move.name} ({move.user_cost_string(self)}), '
                move_list_string += 'Pass\n'
                print(move_list_string)
                decision = ''
                temp_decision = h_input('What will you do? ', 'Move Selection').title()
                if temp_decision != '':
                    # extract choice from list of all options, even if not printed
                    closest_matches = process.extract(temp_decision, options, limit=None)
                    # isolate view commands based on input
                    # inputs without "view" at the start will never be read as a view command (and vice versa)
                    if temp_decision[:4] == 'View':
                        new_closest_matches = []
                        for option in closest_matches:
                            if option[0][:4] == 'View':
                                new_closest_matches.append(option)
                        closest_matches = new_closest_matches
                    else:
                        new_closest_matches = []
                        for option in closest_matches:
                            if option[0][:4] != 'View':
                                new_closest_matches.append(option)
                        closest_matches = new_closest_matches
                    # similarity threshold
                    if closest_matches[0][1] > 70 and closest_matches[0][1] != closest_matches[1][1]:
                        decision = closest_matches[0][0]
            # random move selection
            elif controller == 'Easy':
                print()
                decision = self.choose_move_easy(party, other_party, turn_against_party)
            # calculated move selection
            elif controller == 'Hard':
                print()
                # check for charm switch; if true, uses easy choose move
                if turn_against_party:
                    decision = self.choose_move_easy(party, other_party, turn_against_party)
                else:
                    decision = self.choose_move_hard(party, other_party)
            else:
                raise ValueError(f"Unrecognized controller: {controller}")
            # analyze decisions
            if decision == 'Stop':
                # puts a hard stop to the game
                return 'Stop'
            elif decision[:4] == 'View':
                # quick view of everything
                if decision == 'View':
                    print('\nYour party:')
                    print(party.quick_view())
                    print('Enemy party:')
                    print(other_party.quick_view(len(party) + 1))
                    view_explain_str = "To view a specific demon's details, type "
                    view_explain_str += '"view {demon}", '
                    view_explain_str += "or to view a move's details, type "
                    view_explain_str += '"view {move}".\n'
                    print(view_explain_str)
                # view move
                elif decision[5:] in moves_dict:
                    show_move = False
                    # checks if a friendly or analyzed demon has the move
                    # if not, will print the unknown string
                    for demon in party.demons:
                        if decision[5:] in demon.move_names():
                            show_move = True
                    for demon in other_party.demons:
                        if decision[5:] in demon.move_names() and demon.analyzed:
                            show_move = True
                    # variations of a move will not be shown here (ex. surt fire element attack)
                    # since a new move object is created
                    # would have to distinguish between owners of moves somehow in command
                    # TODO: select demon's move in view command?
                    if show_move:
                        print('\n' + str(Move(decision[5:])))
                    else:
                        print('\n' + Move(decision[5:]).unknown_str())
                # view passive (works same as move)
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
                # shortcut for viewing self (demon)
                elif decision[5:] == 'Self':
                    print('\n' + str(self))
                # show demon by index (shown in plain "view" command)
                elif decision[5:].isnumeric():
                    # search for demon on battlefield by number
                    demon_search_index = int(decision[5:])
                    searching_party = party
                    if demon_search_index > len(party):
                        searching_party = other_party
                        demon_search_index -= len(party)
                    viewing_demon = searching_party.demons[demon_search_index - 1]
                    # check if friendly/analyzed
                    if searching_party == party or viewing_demon.analyzed:
                        print('\n' + str(viewing_demon))
                    else:
                        print('\n' + viewing_demon.unknown_str())
                # search for demon(s) on battlefield by name
                elif decision[5:] in master_list or decision[5:] == 'Demi-Fiend':
                    viewed_demons = []
                    all_demons = party.demons + other_party.demons
                    for demon in all_demons:
                        if decision[5:] == demon.name:
                            viewed_demons.append(demon)
                    view_demon_str = '\n'
                    # notify if more than one demon is found
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
                # normally poison is applied in initiate move, so since that isn't called here, poison is here instead
                self.apply_poison_dmg()
                print()
                return 'Pass'
            elif decision in self.move_names():
                decision_move = self.get_move(decision)
                # verify costs
                # mainly for player; comps should check this beforehand
                if decision_move.mp <= self.mp:
                    if decision_move.hp_cost(self) < self.hp:
                        # call appropriate target choosing method
                        if controller == 'Player':
                            target = self.choose_target(decision_move, party, other_party)
                        elif controller == 'Easy':
                            target = self.choose_target_easy(decision_move, party, other_party)
                        elif controller == 'Hard':
                            # placeholder
                            target = self.choose_target_easy(decision_move, party, other_party)
                        else:
                            raise ValueError(f"Unrecognized controller: {controller}")
                        # if target is "back", will finish while loop and return to move selection
                        if target != 'back':
                            # call initiate move
                            print('******************************************************************')
                            print(f'{self.name} used {decision_move.name}!')
                            press_turns = self.initiate_move(decision_move, target, other_party, kagutsuchi,
                                                             turn_against_party)
                            print('******************************************************************\n')
                            # reset charm effect
                            if turn_against_party:
                                other_party.add_demon(self)
                            return press_turns
                    else:
                        # if the demon has 0 health, no HP costs will be satisfied
                        # will trigger infinite loop
                        if self.hp <= 0:
                            raise RuntimeError('Dead demon encountered in active party.')
                        print('Not enough HP.')
                else:
                    print('Not enough MP.')
            else:
                print('Unrecognized input.\n')

    def unknown_str(self) -> str:
        """
        Modified __str__ method that obscures significant info. Called when the user has no information
        about this demon.

        :return: A string formatted like __str__, but with question marks.
        """
        output = f'Demon: {self.race} {self.name}'
        if self.dead:
            output += ' DEAD'
        output += f', Level ???\n\n'
        if self.magatama is not None:
            output += f'Magatama: ???\n\n'
        output += f'HP: ???/??? MP: ???/???\n\n'
        output += f'Moves: ???\n\n'
        output += f'Passives: ???\n\n'
        barrier_name_list = []
        if self.tetrakarn:
            barrier_name_list.append('Tetrakarn')
        if self.makarakarn:
            barrier_name_list.append('Makarakarn')
        if self.tetraja:
            barrier_name_list.append('Tetraja')
        output += f'Barriers: {", ".join(barrier_name_list) or "None"}\n'
        output += f'Status: {", ".join(self.list_statuses()) or "None"}\n\n'
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

    def __str__(self) -> str:
        """
        Overrides the string representation of Demon. Gives info about the demon, including inherent and temporary
        attributes.

        :return: A string containing info about the demon.
        """
        output = f'Demon: {self.race} {self.name}'
        if self.dead:
            output += ' DEAD'
        output += f', Level {self.level}\n\n'
        if self.magatama is not None:
            output += f'Magatama: {self.magatama}\n\n'
        output += f'HP: {self.hp}/{self.max_hp} MP: {self.mp}/{self.max_mp}\n\n'
        output += f'Moves: {", ".join(self.move_names())}\n\n'
        output += f'Passives: {", ".join(self.passive_names()) or "None"}\n\n'
        barrier_name_list = []
        if self.tetrakarn:
            barrier_name_list.append('Tetrakarn')
        if self.makarakarn:
            barrier_name_list.append('Makarakarn')
        if self.tetraja:
            barrier_name_list.append('Tetraja')
        output += f'Barriers: {", ".join(barrier_name_list) or "None"}\n'
        output += f'Status: {", ".join(self.list_statuses()) or "None"}\n\n'
        output += f'Taru: {self.taru_total()} (+{self.taru_plus}/-{self.taru_minus})\n'
        output += f'Maka: {self.maka_total()} (+{self.maka_plus}/-{self.maka_minus})\n'
        output += f'Raku: {self.raku_total()} (+{self.raku_plus}/-{self.raku_minus})\n'
        output += f'Suku: {self.suku_total()} (+{self.suku_plus}/-{self.suku_minus})\n\n'
        output += f'Strength: {self.str}\n'
        output += f'Magic: {self.mag}\n'
        output += f'Vitality: {self.vit}\n'
        output += f'Agility: {self.ag}\n'
        output += f'Luck: {self.luck}\n\n'
        output += f'Reflects: {", ".join(self.reflect) or "None"}\n'
        output += f'Absorbs: {", ".join(self.absorb) or "None"}\n'
        output += f'Voids: {", ".join(self.void) or "None"}\n'
        output += f'Resists: {", ".join(self.resist) or "None"}\n'
        output += f'Weaknesses: {", ".join(self.weak) or "None"}\n'
        return output


class DemiFiend(Demon):
    """
    Subclass of Demon. Represents a Demi-Fiend, a special type of demon. Overrides methods involved in the creation
    of the demon, notably dict_pull_init.
    """

    def __init__(self, magatama: Optional[str] = None, target_lv: Optional[int] = None,
                 party: Optional[Party] = None) -> None:
        """
        Constructor for the Demi-Fiend class.

        :param magatama: The desired magatama of the Demi-Fiend. If not specified, chooses a random magatama.
        :param target_lv: The target level of the Demi-Fiend. Relevant only if name is not specified and thus a
            magatama will be chosen randomly. If name is not specified and target_lv is, the level of the randomly
            created Demi-Fiend will be close to the target level.
        :param party: The party to which the Demi-Fiend belongs.
        """
        super().__init__(magatama, target_lv=target_lv, party=party)

    def dict_pull_init(self, name: Optional[str], target_lv: Optional[int]) -> None:
        """
        Overriden subset of __init__ method. Sets all "info" attributes, such as name, stats, moves, etc. based on
        magatama_dict.

        :param name: The name of the magatama. If not specified, chooses a random magatama.
        :param target_lv: The target level of a randomly generated magatama. Only used if name is not specified.
        """
        self.name = 'Demi-Fiend'
        # find magatama levels is the level at which its last move is learned
        all_magatama = {n: info['Moves'][-1][1] for n, info in magatama_dict.items()}
        # masakados has to be manually adjusted; all its moves are level 1
        all_magatama['Masakados'] = 95
        # random selection
        if name is None:
            if target_lv is None:
                # select randomly from any magatama
                possible_magatamas = list(all_magatama.keys())
            else:
                # filter magatamas to be within target level range
                possible_magatamas = []
                for magatama, level in all_magatama.items():
                    if level < target_lv + RANDOM_DEMON_RANGE:
                        if level > target_lv - RANDOM_DEMON_RANGE:
                            possible_magatamas.append(magatama)
                if len(possible_magatamas) == 0:
                    # possible if target level plus random range < 19 or > 95 (min/max levels of magatama)
                    # if true, chooses from a few of the lowest/highest level magatama
                    all_sorted_magatama = sorted(all_magatama.items(), key=lambda x: x[1])
                    all_sorted_magatama = [n[0] for n in all_sorted_magatama]
                    if 99 - target_lv > 50:  # small target level
                        possible_magatamas = all_sorted_magatama[:3]
                    else:  # large target level
                        possible_magatamas = all_sorted_magatama[-2:]
            name = random.choice(possible_magatamas)
        self.magatama = name
        self.level = all_magatama[name]
        # find race
        magatama_levels = list(all_magatama.values())
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
        # skills include all of current magatama plus random lower-level skills
        moves = magatama_dict[name]['Moves']
        # filter unimplemented moves
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
        # add pierce to possibilities (not in any magatama)
        possible_moves.append(('Pierce', 1))
        random.shuffle(possible_moves)
        # fill moves, so that demi-fiend always has 8
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
        # create Moves
        for move in moves:
            if move[0] in moves_dict and move[0] not in self.move_names():
                self.moves.append(Move(move[0]))
            if move[0] in passives_dict and move[0] not in self.passive_names():
                self.passives.append(Passive(move[0]))
        # all demi-fiends get Summon
        self.moves.append(Move('Summon'))
        # determine stats
        # modifiers from magatama
        str_mod = magatama_dict[name]['Strength']
        mag_mod = magatama_dict[name]['Magic']
        vit_mod = magatama_dict[name]['Vitality']
        ag_mod = magatama_dict[name]['Agility']
        luck_mod = magatama_dict[name]['Luck']
        # base stats
        self.str = 2 + str_mod
        self.mag = 2 + mag_mod
        self.vit = 2 + vit_mod
        self.ag = 2 + ag_mod
        self.luck = 2 + luck_mod
        stats = ['str', 'mag', 'vit', 'ag', 'luck']
        # used for weighting random selection
        stat_weights = [str_mod, mag_mod, vit_mod, ag_mod, luck_mod]
        stat_weights = [n + 3 for n in stat_weights]
        # assign 1 point per level-up
        for i in range(self.level - 1):
            deciding = True
            while deciding:
                # more likely to choose stats with higher mods from the magatama
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
                elif stat_choice == 'luck' and self.luck < 40:
                    self.luck += 1
                    deciding = False
                else:
                    # if all stats are 40
                    deciding = False
        # resistances
        self.reflect = set(magatama_dict[name]['Reflect'])
        self.absorb = set(magatama_dict[name]['Absorb'])
        self.void = set(magatama_dict[name]['Void'])
        self.resist = set(magatama_dict[name]['Resist'])
        self.weak = set(magatama_dict[name]['Weaknesses'])
        self.evolution = None
        self.calc_init()


class Rotation:
    """
    Contains the order in which demons in a party will act. Includes methods for manipulating and analyzing
    the order.
    """

    def __init__(self, party: Party) -> None:
        """
        Constructor for Rotation.

        :param party: The party to base the rotation on.
        """
        self.party = party
        # boolean indicates whether the demon has gone in the current round or not
        # using lists instead of tuples to be able to edit booleans
        self.order = [[demon, False] for demon in self.party.demons]

    def next(self) -> Demon:
        """
        Gets the next demon in the rotation. Shifts the rotation. If the Rotation is empty, raises an IndexError.

        :return: The next demon to act.
        """
        for demon_info in self.order:
            # check if demon hasn't gone yet
            if not demon_info[1]:
                demon_info[1] = True
                return demon_info[0]
        # if all have gone: reset list
        for demon_info in self.order:
            demon_info[1] = False
        # return first demon in list
        self.order[0][1] = True
        return self.order[0][0]

    def reset(self) -> None:
        """
        Resets the rotation. Also updates the included demons to match that of the linked party.
        For use in between turns.
        """
        self.update()
        self.order = [[demon_info[0], False] for demon_info in self.order]

    def update(self) -> None:
        """
        Updates the rotation to match the demons in the party. For use when a demon is added or removed from the party,
        typically in the middle of a round. Unlike reset, does not adjust which demons have gone.
        """
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

    def __str__(self) -> str:
        """
        String representation of a Rotation. Contains the demons' names in order.

        :return: A string containing info about the rotation.
        """
        return ", ".join([demon[0].name for demon in self.order])


class Party:
    """
    Represents a party of demons. Mainly a wrapper for a list of demons, but also contains info such as a stock
    and a rotation. Methods primarily get info about the demons.
    """

    def __init__(self, demons: List[Demon]) -> None:
        """
        Constructor for Party.

        :param demons: A list of demons to include in the Party.
        """
        self.demons = sorted(demons, key=lambda x: x.ag, reverse=True)  # sorts by agility
        # sets the demon's party attributes
        for demon in self.demons:
            demon.party = self
        self.stock = []
        self.party_stat_calc()  # defines party lv/ag/luck
        self.rotation = Rotation(self)

    def list_demon_names(self) -> List[str]:
        """
        Gets a list of the names of the demons in the Party.

        :return: A list containing the names of each demon in the Party.
        """
        return [demon.name for demon in self.demons]

    def party_stat_calc(self) -> None:
        """
        Used to calculate party-wide stats for selecting random demons (level) and who_goes_first
        (agility+luck). Separate from __init__ in order to call when adding/removing demons.
        """
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
            # if party is empty: default to zeroes
            self.level = level
            self.ag = ag
            self.luck = luck

    def demifiend_in_party(self) -> bool:
        """
        Checks if one or more Demi-Fiends are in the Party.

        :return: True if a Demi-Fiend is in the Party, False otherwise.
        """
        df_in_party = False
        for demon in self.demons:
            if demon.magatama is not None:
                df_in_party = True
        return df_in_party

    def add_demon(self, demon: Demon) -> bool:
        """
        Adds a demon to the active demons list. Updates party info based on the demon.

        :param demon: The demon to add to the active party.
        :return: True if the demon was added successfully, False if the demon was already in the active party.
        """
        if demon not in self.demons:
            self.demons.append(demon)
            demon.party = self
            self.party_stat_calc()
            self.demons.sort(key=lambda x: x.ag, reverse=True)
            self.rotation.update()
            return True
        return False

    def remove_demon(self, demon):
        """
        Removes a demon from the active party. Updates party info.

        :param demon: The demon to remove from the active party.
        :return: True if the demon was removed successfully, False if the demon was not found in the active party.
        """
        if demon in self.demons:
            self.demons.remove(demon)
            self.party_stat_calc()
            self.rotation.update()
            return True
        return False

    def random_targets(self, max_hits: int) -> List[Demon]:
        """
        Gets a list of random demons. Called when a random-target move is used and targets this Party. Isn't strictly
        random; method varies based on the number of demons in the party and the input value.

        :param max_hits: The maximum number of hits for the move.
        :return: A list of random targets, no longer than max_hits.
        """
        targets = []
        target_lists = []
        for demon in self.demons:
            target_lists.append([demon, 0])
        # decide how many hits actually happen
        if len(target_lists) == 1:
            # if only one possible target: chance to hit either one or two times
            random_target_num = random.randint(1, 2)
        elif max_hits == 4:
            # does this also depend on number of enemies? no data about it
            random_target_num = random.randint(2, 4)
        elif max_hits == 5:
            # not strictly random: weighted slightly
            # formula is an approximation
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
                # if each demon has two targets, stop
                if 0 not in max_target_check or 1 not in max_target_check:
                    choosing = False
                random_index = random.randint(0, len(target_lists) - 1)
                # each demon can't be targeted more than twice
                if target_lists[random_index][1] < 2:
                    target_lists[random_index][1] += 1
                    choosing = False
                break_counter += 1
                if break_counter > 255:
                    # occurs when can't select targets
                    # old cause should be fixed, but leaving just in case
                    # not throwing an error to avoid breaking experiments
                    print('multi-target break!')
                    break
        for target_list in target_lists:
            for i in range(target_list[1]):
                targets.append(target_list[0])
        return targets

    def summonable_demons(self) -> List[Demon]:
        """
        Gets all summonable demons.

        :return: A list of all non-dead demons in the stock.
        """
        return [demon for demon in self.stock if not demon.dead]

    def dead_demons(self) -> List[Demon]:
        """
        Gets all dead demons.

        :return: A list of all dead demons in the stock.
        """
        return [demon for demon in self.stock if demon.dead]

    def summon(self, demon: Demon) -> None:
        """
        Moves a demon from the stock to the active party. If demon is dead or is not in the stock, does nothing.

        :param demon: The demon to summon.
        """
        if demon in self.stock and not demon.dead:
            self.stock.remove(demon)
            self.add_demon(demon)

    def unsummon(self, demon: Demon) -> None:
        """
        Moves a demon from the active party to the stock.

        :param demon: The demon to unsummon.
        """
        if demon in self.demons:
            self.remove_demon(demon)
            self.stock.append(demon)

    def death_update(self) -> None:
        """
        Moves all dead demons in the active party to the stock.
        """
        for demon in self.demons:
            if demon.dead:
                self.stock.append(demon)

        for demon in self.stock:
            if demon in self.demons:
                self.remove_demon(demon)

    def lose_check(self) -> bool:
        """
        Checks if the party has lost.

        :return: True if the party has no demons active, False otherwise.
        """
        if len(self) == 0:
            return True
        return False

    def heal(self) -> None:
        """
        Fully heals and summons all demons. Mainly used between games.
        """
        dead_demons = []
        for demon in self.stock:
            dead_demons.append(demon)
        # necessary to avoid iteration skips, since summon removes from stock
        for demon in dead_demons:
            demon.hp = 1
            demon.dead = False
            self.summon(demon)
        for demon in self.demons:
            demon.heal()

    def soft_reset(self) -> None:
        """
        Gets rid of buffs/debuffs, temporary statuses, etc. Calls the soft_reset method for each demon in the party.
        Mainly used between games.
        """
        for demon in self.demons + self.stock:
            demon.soft_reset()

    def __len__(self) -> int:
        """
        Overrides the len() method to return the length of the active party list.

        :return: The length of self.demons
        """
        return len(self.demons)

    def view_targets(self) -> str:
        """
        Generates a string that lists the valid alive targets in the active party.

        :return: A string containing info on the party.
        """
        target_string = f'Valid targets: '
        target_info = [f'[{i}] {demon.name} (HP: {demon.hp}/{demon.max_hp})' for i, demon in enumerate(self.demons, 1)]
        if len(target_info) >= 1:
            target_string += ', '.join(target_info) + '\n'
        else:
            target_string += 'None\n'
        return target_string

    def view_dead_targets(self) -> str:
        """
        Generates a string that lists the valid dead targets in the party.

        :return: A string containing info on the party.
        """
        target_string = f'Valid targets: '
        target_info = [f'[{i}] {demon.name}' for i, demon in enumerate(self.dead_demons(), 1)]
        if len(target_info) >= 1:
            target_string += ', '.join(target_info) + '\n'
        else:
            target_string += 'None\n'
        return target_string

    def view_stock_targets(self) -> str:
        """
        Generates a string that lists the valid alive targets in the stock.

        :return: A string containing info on the party.
        """
        target_string = f'Valid targets: '
        target_info = [f'[{i}] {demon.name} (HP: {demon.hp}/{demon.max_hp})'
                       for i, demon
                       in enumerate(self.summonable_demons(), 1)]
        if len(target_info) >= 1:
            target_string += ', '.join(target_info) + '\n'
        else:
            target_string += 'None\n'
        return target_string

    def quick_view(self, start_label=1) -> str:
        """
        Generates a string with a short description of each demon in the active party. Called mainly during the
        "View" command.

        :param start_label: The number at which to start labeling the demons.
        :return: A string containing info about the party.
        """
        output = ''
        for demon in self.demons:
            demon_desc = f'[{self.demons.index(demon) + start_label}] '
            demon_desc += f'{demon.name} HP: {demon.hp}/{demon.max_hp} MP: {demon.mp}/{demon.max_mp}'
            if len(demon.statuses) >= 1:
                demon_desc += f' Status: {demon.list_statuses()}'
            output += demon_desc + '\n'
        return output

    def __str__(self) -> str:
        """
        Overrides string representation of a Party. Prints each demon in the active party.

        :return: A string containing info about the party.
        """
        output = ''
        for demon in self.demons:
            output += f'{demon}\n'
        return output


class PressTurns:
    """
    Represents a cycle of press turns, used during a party's turn. Includes methods for interacting with the press
    turns.
    """

    def __init__(self, party: Party) -> None:
        """
        Constructor for PressTurns.

        :param party: The party for which to create the PressTurns object.
        """
        self.max_turns = len(party)
        self.full_turns = len(party)
        self.half_turns = 0

    def subtract_turns(self, n: int) -> None:
        """
        Consumes a given number of full turns. Not compatible with half turns (use subtract_half_turn).

        :param n: The number of turns to take away.
        """
        while n > 0:
            # prioritizes taking away half turns
            if self.half_turns > 0:
                self.half_turns -= 1
                n -= 1
            # if no half turns, moves to full turns
            elif self.full_turns > 0:
                self.full_turns -= 1
                n -= 1
            else:
                break

    def subtract_half_turn(self) -> None:
        """
        Turns a full turn into a half turn. If there are no full turns, consumes a half turn.
        """
        # change full turns to half turns.
        if self.full_turns > 0:
            self.full_turns -= 1
            self.half_turns += 1
        elif self.half_turns > 0:
            self.half_turns -= 1

    def pass_turn(self) -> None:
        """
        Turns a full turn into a half turn. Unlike subtract_half_turn, prioritises taking away half-turns
        over converting full turns.
        """
        if self.half_turns > 0:
            self.half_turns -= 1
        elif self.full_turns > 0:
            self.full_turns -= 1
            self.half_turns += 1

    def use_turn(self, turns_used: Union[str, float]) -> None:
        """
        Consumes the given number of turns. Use this method for external calls to update PressTurns;
        relegates specific tasks to the other methods.

        :param turns_used: The number of turns used. Can be the strings 'All' or 'Pass', the float 0.5, or an integer.
        """
        if turns_used == 'All':
            self.subtract_turns(self.max_turns)
        elif turns_used == 'Pass':
            self.pass_turn()
        elif turns_used == 0.5:
            self.subtract_half_turn()
        else:
            self.subtract_turns(turns_used)

    def check_turns(self) -> bool:
        """
        Checks if the object has turns remaining.

        :return: True if there are turns left, False otherwise.
        """
        if self.full_turns == 0 and self.half_turns == 0:
            return False
        return True

    def __str__(self):
        """
        String representation of PressTurns. Indicates how many full turns and half turns remain out of the total.

        :return: A string containing info about the PressTurns object.
        """
        output = []
        for i in range(self.max_turns - (self.full_turns + self.half_turns)):  # used turns
            output.append('O')
        for i in range(self.half_turns):
            output.append('*')
        for i in range(self.full_turns):
            output.append('X')
        return str(output)


class FourVsFour:
    """
    Represents a game as an object. Methods allow for party creation, parameter setting, and gameplay (through turn
    cycle control). Not necessarily four demons vs four demons— can vary based on input.
    """

    def __init__(self, kagutsuchi: Kagutsuchi = Kagutsuchi()) -> None:
        """
        Constructor for a FourVsFour game.

        :param kagutsuchi: The Kagutsuchi at which to start the game. Random if not specified.
        """
        self.kagutsuchi = kagutsuchi
        self.party1 = Party([])
        self.party2 = Party([])
        self.controllers = ['Player', 'Comp']
        self.ran = False
        self.difficulties = ['Easy']
        self.turns = 0
        self.match_party1_length = False
        self.stopped_game = False

    def select_players(self) -> None:
        """
        Selects the controllers (player or comp) and the difficulty of the comp based on player input. Updates
        internal attributes.
        """
        player_options = ['Player vs. Comp', 'Player vs. Player', 'Comp vs. Comp']
        print(f'The current player options are as follows: {", ".join(player_options)}')
        selected_mode = h_input('Select a mode: ', "Player Select")
        if selected_mode != '':  # defaults to player vs comp (defined in init)
            selected_mode = process.extractOne(selected_mode, player_options)[0]
            if selected_mode == 'Player vs. Player':
                self.controllers[1] = 'Player'
            elif selected_mode == 'Comp vs. Comp':
                self.controllers[0] = 'Comp'
        # set difficulties
        for i in range(len(self.controllers)):
            if self.controllers[i] == 'Comp':
                if len(self.difficulties) > 1:
                    input_str = 'Select the difficulty of the '
                    if self.controllers.count('Comp') > 1:
                        input_str += ordinal(i + 1)
                    input_str += f'comp ({", ".join(self.difficulties)}): '
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
                            # if this is the first controller, picks a random difficulty
                            selected_difficulty = random.choice(self.difficulties)
                    else:
                        selected_difficulty = process.extractOne(selected_difficulty, self.difficulties)[0]
                    self.controllers[i] = selected_difficulty
                else:
                    # doesn't ask player if only 1 difficulty implemented
                    self.controllers[i] = self.difficulties[0]

    def create_player_party(self, party: Party, target_lv: Optional[int] = None) -> None:
        """
        Creates a party based on player input.

        :param party: The party to add demons to.
        :param target_lv: The target level for any random demons added. Default is random.
        """
        demons = []
        random_party = False
        if self.match_party1_length:
            demon_count = len(self.party1)
        else:
            demon_count = 4 - len(party)
        for i in range(demon_count):
            player_input = h_input(f'Choose the {ordinal(i + 1)} demon in your party: ', 'Choosing a Party').lower()
            # choose randomly
            if player_input == 'random':
                random_party = True
                break
            elif player_input == '':
                if len(demons) < 1:
                    # shortcut for random party (if no demons selected)
                    random_party = True
                else:
                    # ends demon selection (party can't be empty)
                    # when true, future create party calls will match the length of party 1 instead of defaulting to 4
                    self.match_party1_length = True
                break
            # if number, use that as the target level in random generation
            elif player_input.isnumeric() and 1 <= int(player_input) <= 99:
                target_lv = int(player_input)
                random_party = True
                break
            # choose demon
            else:
                player_input = process.extractOne(player_input, master_list)[0]
                # find devolution
                player_input, evolve = find_evolve_count(player_input)
                if player_input in demon_dict:
                    demons.append(Demon(player_input, evolutions=evolve))
                    print(f'{player_input} added.')
                elif player_input in magatama_dict:
                    demons.append(DemiFiend(player_input))
                    print(f'Demi-Fiend {f"({player_input}) " if player_input else ""}added.')
                else:
                    # shouldn't really happen since the extractOne is being run from the master_list
                    raise ValueError(f'Input could not be found in the database: {player_input}')
        for demon in demons:
            party.add_demon(demon)
        if random_party:
            self.create_random_party(party, target_lv=target_lv)

    def create_random_party(self, party: Party, target_lv: Optional[int] = None) -> None:
        """
        Creates a party randomly. Can add on to partially-filled parties as well.

        :param party: The party to add demons to.
        :param target_lv: The target level for the random demons added. Default is random.
        """
        if self.match_party1_length:
            party_length = len(self.party1)
        else:
            party_length = 4
        if len(party) == 0:
            party.add_demon(DemiFiend(target_lv=target_lv, party=party))
        # following if statement is to make sure level selection adheres to parameter instead of current party lv
        if target_lv is None:  # unspecified target level: uses party level average
            if len(party) < party_length and not party.demifiend_in_party():
                party.add_demon(DemiFiend(target_lv=party.level, party=party))
            while len(party) < party_length:
                party.add_demon(Demon(target_lv=party.level, party=party))
        else:  # specified target level
            if len(party) < party_length and not party.demifiend_in_party():
                party.add_demon(DemiFiend(target_lv=target_lv, party=party))
            while len(party) < party_length:
                party.add_demon(Demon(target_lv=target_lv, party=party))

    def who_goes_first(self) -> int:
        """
        Decides randomly which party will go first.

        :return: 1 if party 1 goes fist, 2 if party 2 goes first.
        """
        # this formula is adjusted to give an even chance to both teams
        # for the in-game formula, see the Endurance overriden version
        party1_chance = 50 + self.party1.level + (self.party1.luck / 2) + self.party1.ag
        party1_chance -= self.party2.level + (self.party2.luck / 2) + self.party2.ag
        if random.randint(0, 100) <= party1_chance:
            return 1
        return 2

    def player_turn(self, party: Party, other_party: Party) -> bool:
        """
        Runs a turn where the player is in control. Takes in player input. Calls Demon.action until a PressTurns object
        is empty.

        :param party: The acting party, to be controlled by player input.
        :param other_party: The opposing party.
        :return: True if the game should end, False otherwise.
        """
        press_turns = PressTurns(party)
        if self.controllers[0] == 'Player' and self.controllers[1] in self.difficulties:
            print('Your turn!\n')
        else:
            # doesn't print "your turn" if there are two players or two comps
            if party == self.party1:
                print("Player 1's turn!\n")
            else:
                print("Player 2's turn!\n")
        # cure statuses and reset rotation
        for demon in party.demons:
            demon.tick_statuses()
        party.rotation.reset()
        while press_turns.check_turns() and not self.check_victory():
            print(f'Press turns: {press_turns}   Kagutsuchi: {str(self.kagutsuchi)}')
            print('Demon order:', party.rotation)
            # main call: updates rotation and takes action
            used_turns = party.rotation.next().action(party, other_party, 'Player', self.kagutsuchi)
            if used_turns == 'Stop':
                # break out of loop if "Stop" was inputted
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

    def comp_turn(self, party: Party, other_party: Party, difficulty: str) -> bool:
        """
        Runs a turn where the computer is in control. Calls Demon.action until a PressTurns object is empty.

        :param party: The acting party.
        :param other_party: The opposing party.
        :param difficulty: Specifies the type of AI to use in action selection.
        :return: True if the game should end, False otherwise.
        """
        # mainly differs from player turn in the difficulty specification to action()
        # also cuts some player-only logic, such as the "Stop" catch
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
        while press_turns.check_turns() and not self.check_victory():
            print(f'Press turns: {press_turns}    Kagutsuchi: {str(self.kagutsuchi)}')
            press_turns.use_turn(party.rotation.next().action(party, other_party, difficulty, self.kagutsuchi))
            other_party.death_update()
            party.death_update()
        if self.check_victory():
            return True
        print(f'Press turns: {press_turns}\n')
        return False

    def turn(self, party: Party, other_party: Party, controller: str) -> bool:
        """
        Runs a turn. Use this method instead of player_turn or comp_turn. Relegates to those methods based on
        controller parameter.

        :param party: The acting party.
        :param other_party: The opposing party.
        :param controller: The controller of the acting party.
        :return: True if the game should end, False otherwise.
        """
        # stops infinite games
        # can occur without bugs, ex: two demons left absorb phys and have 0 MP
        self.turns += 1
        if self.turns > 255:
            print('Turn limit (255) reached!')
            return True
        if controller == 'Player':
            return self.player_turn(party, other_party)
        else:
            return self.comp_turn(party, other_party, controller)

    def check_victory(self) -> bool:
        """
        Checks if a party has lost. Used for checking when to end the game.

        :return: True if either party has lost, False otherwise.
        """
        if self.party1.lose_check() or self.party2.lose_check():
            return True
        return False

    def heal_parties(self) -> None:
        """
        Heals all parties in the game. Generally used between games, if using the same FourVsFour object.
        """
        self.party1.heal()
        self.party2.heal()

    def run(self) -> dict:
        """
        Sets up and runs the game. Alternates turn calls between parties until one loses.

        :return: A dictionary containing the number of wins for each player, the number of ties, the Kagutsuchi,
            and if the game was force-stopped or not.
        """
        if self.ran:
            # reset between runs if already ran
            self.heal_parties()
            self.turns = 0
            self.stopped_game = False
            self.match_party1_length = False
        else:
            # if first run: select teams
            self.select_players()
            if self.controllers[0] == 'Player':
                self.create_player_party(self.party1)
            else:
                self.create_random_party(self.party1)
            if self.controllers[1] == 'Player':
                # use party 1 level as target
                self.create_player_party(self.party2, target_lv=self.party1.level)
            else:
                self.create_random_party(self.party2, target_lv=self.party1.level)
            self.ran = True
        current_turn = self.who_goes_first()
        victory = False
        # alternate between turn calls until one returns True
        while not victory:
            if current_turn == 1:
                victory = self.turn(self.party1, self.party2, self.controllers[0])
                current_turn = 2
            elif current_turn == 2:
                victory = self.turn(self.party2, self.party1, self.controllers[1])
                current_turn = 1
        # output
        output_dict = {'Player 1 Wins': 0,
                       'Player 2 Wins': 0,
                       'Ties': 0,
                       'Kagutsuchi': self.kagutsuchi,
                       'Stop': self.stopped_game}
        self.kagutsuchi += 1  # increment kagutsuchi
        if self.party1.lose_check():
            # conditional prints based on controllers (like in player_turn and comp_turn)
            if self.controllers[0] == 'Player' and self.controllers[1] in self.difficulties:
                print('You lost.')
            else:
                print('Player 2 wins!')
            output_dict['Player 2 Wins'] += 1
        elif self.party2.lose_check():
            if self.controllers[0] == 'Player' and self.controllers[1] in self.difficulties:
                print('You won!')
            else:
                print('Player 1 wins!')
            output_dict['Player 1 Wins'] += 1
        else:
            print('Tie!')
            output_dict['Ties'] += 1
        return output_dict


class AutoFourVsFour(FourVsFour):
    """
    Modified FourVsFour subclass to allow for automated runs without any player input.
    """

    def __init__(self, info: dict, kagutsuchi: Kagutsuchi = Kagutsuchi()) -> None:
        """
        Constructor for AutoFourVsFour.

        :param info: A dict containing info about how the game should be run. Should contain info about demons,
            controllers, and target levels. Created in experiment().
        :param kagutsuchi: The Kagutsuchi at which to start the game. Random if not specified.
        """

        super().__init__(kagutsuchi)
        self.info = info
        self.party1.heal()
        self.party2.heal()

    def select_players(self) -> None:
        """
        Selects the players involved in the game based on the info attribute. Overriden from base class to remove
        player input.
        """
        if 'Controller 1' in self.info:
            self.controllers[0] = self.info['Controller 1']
        else:
            self.controllers[0] = self.difficulties[0]
        if 'Controller 2' in self.info:
            self.controllers[1] = self.info['Controller 2']
        else:
            self.controllers[1] = self.difficulties[0]

    def create_random_party(self, party: Party, target_lv: Optional[int] = None):
        """
        Creates a party randomly. Can add on to partially-filled parties as well. Overriden from base class to
        use demons and target levels from the info attribute (if specified).

        :param party: The party to add demons to.
        :param target_lv: The target level for the random demons added. Will be overriden by the info attribute
            if that is specified. Default is random.
        """
        # adds demons to parties based on info dict
        for demon in self.info['Demons 1']:
            self.party1.add_demon(demon)
        for demon in self.info['Demons 2']:
            self.party2.add_demon(demon)
        if party == self.party1 and self.info['Target Level 1'] is not None:
            super().create_random_party(party, target_lv=self.info['Target Level 1'])
        elif party == self.party2 and self.info['Target Level 2'] is not None:
            super().create_random_party(party, target_lv=self.info['Target Level 2'])
        else:
            super().create_random_party(party, target_lv=target_lv)


class Endurance(FourVsFour):
    """
    Extends the FourVsFour class. Changes the rules so that Party 1's demons are not healed between battles
    and the game continues until Party 1 loses.
    """

    def heal_parties(self) -> None:
        """
        Creates a new party for Party 2. Overrides the base class to remove healing for Party 1 and to remake Party 2
        each game instead of healing the same party. Generally used between games.
        """
        # removes temp statuses, debuffs, etc. from Party 1 (but no full reset or heal)
        self.party1.soft_reset()
        # ticks poison once between games
        for demon in self.party1.demons:
            demon.apply_poison_dmg()
        # creates new Party 2
        self.party2 = Party([])
        self.create_random_party(self.party2, target_lv=self.party1.level)

    def who_goes_first(self) -> int:
        """
        Decides randomly which party will go first. Overriden from base class to favor Party 1.

        :return: 1 if party 1 goes fist, 2 if party 2 goes first.
        """
        # this formula matches the base game, except for back attacks
        # higher base chance (72) and chance is clamped between 50 and 85
        party1_chance = 72 + self.party1.level + (self.party1.luck / 2) + self.party1.ag
        party1_chance -= self.party2.level + (self.party2.luck / 2) + self.party2.ag
        if party1_chance > 85:
            party1_chance = 85
        elif party1_chance < 50:
            party1_chance = 50
        if random.randint(0, 100) <= party1_chance:
            return 1
        return 2

    def run(self) -> dict:
        """
        Sets up and runs the game. Overriden from the base class in order to keep running games until Party 1 loses.

        :return: A dictionary containing the number of wins for each player, the number of ties, the Kagutsuchi,
            and if the game was force-stopped or not.
        """
        party1_alive = True
        output_dict = {'Player 1 Wins': 0, 'Player 2 Wins': 0, 'Ties': 0}
        while party1_alive:
            game_output = super().run()
            for point_total in output_dict.keys():
                output_dict[point_total] += game_output[point_total]
            if self.stopped_game:
                break
            elif output_dict['Player 2 Wins'] >= 1:
                party1_alive = False
            else:
                print(f'Current score: {output_dict["Player 1 Wins"]}')
        output_dict['Kagutsuchi'] = game_output['Kagutsuchi']
        output_dict['Stop'] = self.stopped_game
        return output_dict


class AutoEndurance(Endurance, AutoFourVsFour):
    """
    Allows the Endurance game mode to run without player input, similarly to AutoFourVsFour.
    """
    # neither of the methods overriden by the classes override each other, so this just works
    pass


def experiment() -> None:
    """
    Runs an experiment. Reads the external file database/experiment-settings.json and takes in user input to set
    experiment parameters, and then runs games automatically according to those parameters.
    """
    print('\nEntering experiment mode...\n')
    # when adding new game modes, add them to this list
    # different from the main() list because they have to be separately implemented into experiment
    game_modes = ['4 vs. 4', 'Endurance']
    p1_wins = 0
    p2_wins = 0
    ties = 0
    # create one copy to change and one copy to hold defaults (avoid loading each time)
    with open('database/experiment-settings.json') as f:
        default_test_info = json.load(f)
    # don't need a deepcopy since all values in the json are primitives
    test_info = copy.copy(default_test_info)
    # setting changing
    settings_names = list(test_info.keys())
    while True:
        # print settings and values
        settings_display = ''
        for s_name in settings_names:
            if 'Demons' in s_name:
                names = [f'Demi-Fiend ({x.magatama})' if x.magatama is not None else x.name for x in test_info[s_name]]
                settings_display += f'{s_name}: {names}\n'
            else:
                settings_display += f'{s_name}: {test_info[s_name]}\n'
        print(f'Settings:\n{settings_display}')
        # select setting to change
        changing_setting = h_input('Choose a setting to change or press enter: ', 'Settings Overview')
        if changing_setting == '':
            break
        else:
            changing_setting = process.extractOne(changing_setting, settings_names + ['Default'])[0]
        # set the number of trials
        # each elif clause sets the variable setting_val— it will be assigned to the dict at the end
        if changing_setting == 'Trials':
            valid_input = False
            while not valid_input:
                setting_val = h_input('Enter the number of trials: ', 'Set Trials')
                # empty input goes to default
                if setting_val == '':
                    setting_val = default_test_info['Trials']
                    print(f'The number of trials will be set to the default value.')
                    valid_input = True
                # check if positive integer
                elif setting_val.isnumeric():
                    setting_val = int(setting_val)
                    if setting_val >= 1:
                        valid_input = True
                    else:
                        print('The number must be greater than or equal to 1.\n')
                else:
                    print('The input must be numeric.\n')
            print(f'Trial number set to {setting_val}.')
        # set the game mode
        elif changing_setting == 'Game Mode':
            if len(game_modes) > 1:
                valid_input = False
                while not valid_input:
                    print(f'The current game modes are as follows: {", ".join(game_modes)}')
                    setting_val = h_input('Enter a game mode: ', 'Set Game Mode')
                    # empty default
                    if setting_val == '':
                        setting_val = default_test_info['Game Modes']
                        print(f'The game mode will be set to the default.')
                        valid_input = True
                    else:
                        setting_val = process.extractOne(setting_val, game_modes)[0]
                        valid_input = True
            else:
                # if there is only one game mode, don't bother asking
                print(f'Only one game mode is available ({game_modes[0]}).')
                setting_val = game_modes[0]
            print(f'Game mode set to {setting_val}.')
        # set whether teams remain the same between games
        elif changing_setting == 'Same Teams':
            valid_input = False
            while not valid_input:
                setting_val = h_input('Use the same teams every battle? (y/n): ', 'Set Same Teams').lower()
                # default
                if setting_val == '':
                    setting_val = default_test_info['Same Teams']
                    print(f'Team carry-over will be set to the default.')
                    valid_input = True
                # parse y/yes as True and n/no as False
                elif setting_val == 'y' or setting_val == 'yes':
                    setting_val = True
                    valid_input = True
                elif setting_val == 'n' or setting_val == 'no':
                    setting_val = False
                    valid_input = True
                else:
                    print('The input must be "y", "yes", "n", or "no".\n')
            # for boolean settings, using inline if else to print info
            print(f'Teams set to {"carry over" if setting_val else "remake"} after each battle.')
        # set the target level of Party 1
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
                    setting_val = None
                else:
                    print('The input must be numeric or "None".\n')
            print(f'Target level for party 1 set to {setting_val}.')
        # set the target level of Party 2 (same as Target Level 1)
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
                    setting_val = None
                else:
                    print('The input must be numeric or "None".\n')
            print(f'Target level for party 2 set to {setting_val}.')
        # set the specific demons to be included in Party 1
        # note that since this creates non-primitives, the json default can't be changed (has to be empty list)
        # would be doable with the demon-string creator in the below todo
        elif changing_setting == 'Demons 1':
            setting_val = []
            while len(setting_val) < 4:
                demon_input = h_input(f'Choose the {ordinal(len(setting_val) + 1)} demon in party 1: ', 'Set Demons')
                # end selection if blank input
                if demon_input == '':
                    break
                # create demon based on input (like in create random party)
                # TODO: make a function that creates a demon from a string
                # prevent repetition between here and FourVsFour class
                demon_input = process.extractOne(demon_input, master_list)[0]
                demon_input, evolve = find_evolve_count(demon_input)
                if demon_input in demon_dict:
                    setting_val.append(Demon(demon_input, evolutions=evolve))
                    print(f'{setting_val[-1].name} was added to party 1.')
                elif demon_input in magatama_dict:
                    setting_val.append(DemiFiend(demon_input))
                    print(f'{setting_val[-1].name} ({setting_val[-1].magatama}) was added to party 1.')
            # list comp: get names of demons; note demi-fiend's magatama if the demon is a demi-fiend
            sv_demon_names = [f'Demi-Fiend ({x.magatama})' if x.magatama is not None else x.name for x in setting_val]
            print(f'Specified demons in party 1: {", ".join(sv_demon_names)}')
        # set the demons to be included in Party 2 (same as Demons 1)
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
            sv_demon_names = [f'Demi-Fiend ({x.magatama})' if x.magatama is not None else x.name for x in setting_val]
            print(f'Specified demons in party 2: {", ".join(sv_demon_names)}')
        # set the kagutsuchi phase
        elif changing_setting == 'Kagutsuchi Phase':
            valid_phase_input = False
            while not valid_phase_input:
                setting_val = h_input('Enter the kagutsuchi phase (0-8): ', 'Set Kagutsuchi Phase')
                # check if number between 0 and 8
                if setting_val.isnumeric():
                    setting_val = int(setting_val)
                    if 0 <= setting_val <= 8:
                        valid_phase_input = True
                    else:
                        print('The number must be between 0 and 8 (inclusive).\n')
                # also check for "dead" and "random" strings
                elif setting_val.title() == 'Dead':
                    valid_phase_input = True
                    setting_val = 'Dead'
                elif setting_val.title() == 'Random' or setting_val == '':
                    valid_phase_input = True
                    setting_val = 'Random'
                else:
                    print('The input must be numeric, "Dead", or "Random".\n')
            print(f'Kagutsuchi phase set to {setting_val}.')
        # set whether kagutsuchi rotates or not
        elif changing_setting == 'Kagutsuchi Freeze':
            valid_frozen_input = False
            while not valid_frozen_input:
                setting_val = h_input('Prevent kagutsuchi phase changes? (y/n): ', 'Set Kagutsuchi Freeze').lower()
                if setting_val == 'y' or setting_val == 'yes':
                    setting_val = True
                    valid_frozen_input = True
                elif setting_val == 'n' or setting_val == 'no' or setting_val == '':
                    setting_val = False
                    valid_frozen_input = True
                else:
                    print('The input must be "y", "yes", "n", or "no".\n')
            print(f'Kagutsuchi set to {"stay the same" if setting_val else "rotate"} between games.')
        # sets whether game info is printed or saved to a file
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
        # sets the name of the file to save logs to
        elif changing_setting == 'File Name':
            valid_input = False
            while not valid_input:
                valid_input = True
                setting_val = h_input('Enter the desired log file name: ', 'Set File Name')
                if setting_val == '':
                    setting_val = default_test_info['File Name']
                    print(f'The file name will be set to the default value.')
                else:
                    # ensure given file name is only letters, numbers, hyphens, and underscores
                    for char in setting_val:
                        if not char.isalpha() and not char.isnumeric():
                            if char != '_' and char != '-':
                                valid_input = False
                if not valid_input:
                    print('The file name must contain only letters and numbers.\n')
            print(f'The game log file will be called "{setting_val}.txt".')
        # reset all settings to their defaults (as loaded in from experiment-settings.json)
        if changing_setting == 'Default':
            print('All settings will be restored to the defaults.')
            confirm_reset = h_input('Type "back" to return or anything else to proceed: ', 'Default Settings')
            if confirm_reset != 'back':
                test_info = copy.copy(default_test_info)
                print('Settings reset to default.')
        else:
            # assign setting_val to the main settings dict
            # if/else here because default doesn't use setting_val
            test_info[changing_setting] = setting_val
        print()
    # game initiation
    exp_kagutsuchi = Kagutsuchi(test_info['Kagutsuchi Phase'], test_info['Kagutsuchi Freeze'])
    if test_info['Game Mode'] == '4 vs. 4':
        game = AutoFourVsFour(test_info, kagutsuchi=exp_kagutsuchi)
    elif test_info['Game Mode'] == 'Endurance':
        game = AutoEndurance(test_info, kagutsuchi=exp_kagutsuchi)
    # redirect standard output to file
    if test_info['Log Games']:
        orig_stdout = sys.stdout
        f = open(f'{test_info["File Name"]}.txt', 'w')
        sys.stdout = f
    # start timer to track elapsed time
    start_time = timeit.default_timer()
    # run games
    for i in range(test_info['Trials']):
        game_info = game.run()
        p1_wins += game_info['Player 1 Wins']
        p2_wins += game_info['Player 2 Wins']
        ties += game_info['Ties']
        # print update (if logging to file)
        if test_info['Log Games']:
            sys.stdout = orig_stdout
            current_time = timeit.default_timer()
            info_str = f'\rGames played: {i + 1}/{test_info["Trials"]}'
            info_str += f'\tElapsed time: {round(current_time - start_time, 3)}s'
            print(info_str, end='')
            sys.stdout = f
        if not test_info['Same Teams']:
            # recreate teams
            game.party1 = Party([])
            game.create_random_party(game.party1)
            game.party2 = Party([])
            game.create_random_party(game.party2, game.party1.level)
    # close/reset output
    if test_info['Log Games']:
        sys.stdout = orig_stdout
        f.close()
        print()
    # print results
    summary_str = f'Total score: {p1_wins} to {p2_wins} ('
    if p1_wins > p2_wins:
        summary_str += 'Player 1 leading'
    elif p2_wins > p1_wins:
        summary_str += 'Player 2 leading'
    else:
        summary_str += 'tied'
    if ties > 0:
        summary_str += f', {ties} ties'
    summary_str += ')'
    # give final time if not in Log Games mode (where time would always be visible)
    if not test_info['Log Games']:
        summary_str += f'\nTotal time: {round(timeit.default_timer() - start_time, 3)}s'
    print(summary_str)


def main() -> None:
    """
    The main function. Allows players to choose game modes and then initializes and runs games. Also controls the
    decision to play again.
    """
    game_modes = ['4 vs. 4', 'Endurance', 'Experiment']
    playing = True
    runback = False
    p1_wins = 0
    p2_wins = 0
    ties = 0
    kagutsuchi = Kagutsuchi()
    print('Welcome to NocturneTS!\nAt any time, type "help" for commands and rule explanations.\n')
    while playing:
        if not runback:
            # select game mode
            print(f'The current game modes are as follows: {", ".join(game_modes)}')
            selected_mode = h_input('Choose a game mode: ', 'Game Modes')
            if selected_mode == '':
                # default to first mode (4 vs 4)
                selected_mode = game_modes[0]
            else:
                selected_mode = process.extractOne(selected_mode, game_modes)[0]
            if selected_mode == '4 vs. 4':
                game = FourVsFour(kagutsuchi=kagutsuchi)
            elif selected_mode == 'Endurance':
                game = Endurance(kagutsuchi=kagutsuchi)
            elif selected_mode == 'Experiment':
                experiment()
                break
        # run game; capture output
        game_info = game.run()
        # tracks wins of each player
        p1_wins += game_info['Player 1 Wins']
        p2_wins += game_info['Player 2 Wins']
        ties += game_info['Ties']
        # print current standings
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
        # auto break if game was manually stopped
        if game_info['Stop']:
            playing = False
        else:
            # ask to play again
            print()
            repeat_decision = h_input('Play again? (y/n) ', 'Game End').lower()
            # could incorporate fuzzywuzzy
            if repeat_decision == 'y' or repeat_decision == 'yes':
                # ask to keep same settings
                runback_decision = h_input('Same teams? (y/n) ', 'Game End').lower()
                if runback_decision == 'y' or runback_decision == 'yes':
                    # if yes: skips setup, just runs game again
                    runback = True
                else:
                    # if no: goes back to the beginning
                    runback = False
            else:
                playing = False


if __name__ == "__main__":
    main()
