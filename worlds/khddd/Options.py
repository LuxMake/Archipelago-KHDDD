#Blank options file; not ready for customization yet
from dataclasses import dataclass
from Options import Choice, Toggle, PerGameCommonOptions, StartInventoryPool, NamedRange, Range

class StartingWorlds(Range):
    """
    Number of random worlds to start with
    """
    display_name = "Starting Worlds"
    default = 1
    range_start = 1
    range_end = 10

class Character(NamedRange):
    """
    Determines whether to play as Sora, Riku, or Both
    0: Both
    1: Sora Only
    2: Riku Only
    """
    display_name = "Character"
    default = 0
    range_start = 0
    range_end = 2
    special_range_names = {
        "both": 0,
        "sora": 1,
        "riku": 2,
    }

class Goal(NamedRange):
    """
    Win Condition
    0: Defeat the Final Boss (Xemnas for Sora and Young Xehanort for Riku
    1: Defeat All Superbosses (Secret Portals and Julius)
    """
    display_name = "Goal"
    default = 0
    range_start = 0
    range_end = 1
    special_range_names = {
        "final_boss": 0,
        "superbosses": 1
    }

class AVN(Toggle):
    """
    If enabled, the win condition for the Final Boss goal is moved to AVN instead of Young Xehanort
    This is ignored if the goal is Superbosses or the player chooses Sora as their character
    """
    display_name = "Armored Ventus Nightmare"

class RecipeReqs(Range):
    """
    Number of Recipes needed to beat the game
    Meow Wow and Komory Bat recipes are always required
    """
    display_name = "Recipes Required"
    default = 2
    range_start = 2
    range_end = 52

class RecipesInPool(Range):
    """
    Number of Recipes in the Item Pool
    Always includes Meow Wow and Komory Bat recipes
    """
    display_name = "Recipes in the Item Pool"
    default = 52
    range_start = 2
    range_end = 52

class Superbosses(Toggle):
    """
    Determines whether Secret Portals and Julius  are checks
    This option is ignored if the Goal is Superbosses
    """

#####################################
#########Quality of Life#############
#####################################
class ExpMultiplier(Range):
    """
    Determines the multiplier to apply to EXP gained
    """
    display_name = "Exp Multiplier"
    default = 2
    range_start = 1
    range_end = 10

class StatBonusAmount(Range):
    """
    Determines how many points each stat increase grants.
    Only applies to Strength, Defense, and Magic increases.
    """
    display_name = "Stat Bonus Amount"
    default = 2
    range_start = 1
    range_end = 5

class StrengthInPool(Range):
    """
    Determines how many strength increases per character are in the item pool.
    Does nothing if Stats On Levels is enabled.
    """
    display_name = "Strength in Pool"
    default = 18
    range_start = 0
    range_end = 50

class MagicInPool(Range):
    """
    Determines how many magic increases per character are in the item pool.
    Does nothing if Stats On Levels is enabled.
    """
    display_name = "Magic in Pool"
    default = 18
    range_start = 0
    range_end = 50

class DefenseInPool(Range):
    """
    Determines how many defense increases per character are in the item pool.
    Does nothing if Stats On Levels is enabled.
    """
    display_name = "Defense in Pool"
    default = 15
    range_start = 0
    range_end = 50

class PlayDestinyIslands(Toggle):
    """
    Allows you to play the Ursula battle at the start of the run.
    This grants 5 additional checks.
    Does nothing if the player chooses Riku as their character.

    NOTE: Need to connect to the server during the intro cutscene
          with Braig in order for this to take effect.
    """
    display_name = "Play Ursula Battle"

class SkipLightCycle(Toggle):
    """
    Allows you to skip the Light Cycle section of Riku's Grid.
    Skipping will still grant the check for clearing the Light Cycle minigame.
    Does nothing if the player chooses Sora as their character.
    """
    display_name = "Skip Light Cycle"

class FastGoMode(Toggle):
    """
    When enabled, the save point for Young Xehanort is
    activated after collecting the necessary key items,
    allowing you to do the final fight instantly without
    having to play the entirety of The World That Never Was.

    Does nothing if the goal is Superbosses or the player
    chooses Sora as their character.
    """
    display_name = "Fast Go Mode"

#####################################
##########Extra Features#############
#####################################
class RandomizeKeybladeStats(Toggle):
    """
    Determines if Keyblade stats should be randomized
    """
    display_name = "Randomize Keyblade Stats"

class KeybladeMinStrength(Range):
    """
    Determines the minimum Strength bonus a keyblade can have
    """
    display_name = "Keyblade Minimum Strength"
    default = 2
    range_start = 0
    range_end = 10

class KeybladeMaxStrength(Range):
    """
    Determines the maximum Strength bonus a keyblade can have
    """
    display_name = "Keyblade Maximum Strength"
    default = 18
    range_start = 11
    range_end = 18

class KeybladeMinMagic(Range):
    """
    Determines the minimum Magic bonus a keyblade can have
    """
    display_name = "Keyblade Minimum Magic"
    default = 2
    range_start = 0
    range_end = 10

class KeybladeMaxMagic(Range):
    """
    Determines the maximum Magic bonus a keyblade can have
    """
    display_name = "Keyblade Maximum Magic"
    default = 16
    range_start = 11
    range_end = 18

class InstantDropTrapChance(Range):
    """
    Determines the % chance a filler item gets replaced by an instant drop trap.
    """
    display_name = "Instant Drop Trap Chance"
    default = 0
    range_start = 0
    range_end = 25

class StatsOnLevels(Toggle):
    """
    Determines whether level checks contain only stat increases.
    """
    display_name = "Stats On Levels"

class SingleFlowmotion(Toggle):
    """
    If enabled, all flowmotion is obtained as a single item
    """
    display_name = "Flowmotion is One Item"

@dataclass
class KHDDDOptions(PerGameCommonOptions):
    character: Character
    goal: Goal
    armored_ventus_nightmare: AVN
    recipe_reqs: RecipeReqs
    recipes_in_pool: RecipesInPool
    starting_worlds: StartingWorlds
    superbosses: Superbosses
    play_destiny_islands: PlayDestinyIslands
    skip_light_cycle: SkipLightCycle
    fast_go_mode: FastGoMode
    exp_multiplier: ExpMultiplier
    stat_bonus: StatBonusAmount
    strength_in_pool: StrengthInPool
    magic_in_pool: MagicInPool
    defense_in_pool: DefenseInPool
    randomize_keyblade_stats: RandomizeKeybladeStats
    keyblade_min_str: KeybladeMinStrength
    keyblade_max_str: KeybladeMaxStrength
    keyblade_min_mag: KeybladeMinMagic
    keyblade_max_mag: KeybladeMaxMagic
    instant_drop_trap_chance: InstantDropTrapChance
    stats_on_levels: StatsOnLevels
    single_flowmotion: SingleFlowmotion

    start_inventory_from_pool: StartInventoryPool