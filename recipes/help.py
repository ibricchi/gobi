from __future__ import annotations

from utils.loader import GobiFile
from utils.recipes import GobiError, Action, Recipe, load_recipe

def surround_print(text: str) -> None:
    str_len = len(text)
    print("#" * (str_len + 4))
    print(f"# {text} #")
    print("#" * (str_len + 4))

class HelpAction(Action):
    def __init__(self) -> None:
        self.name = "help"
        self.subname = "help"

    def help(self) -> None:
        print("Usage: gobi help [recipe|action] [args...]")
        print("       gobi help recipe for help on all loaded recipes")
        print("       gobi help recipe [recipe...] for help on a specific recipe/s")
        print("       gobi help action for help on all loaded actions")
        print("       gobi help action [action...] for help on a specific action/s")

    def run(
        self,
        gobi_file: GobiFile,
        recipes: dict[str, Recipe],
        actions: list[Action],
        args: list[str],
    ) -> GobiError | None:
        if args == []:
            self.help()
        elif args[0] == "recipe":
            if len(args) == 1:
                print("Help for all loaded recipes:")
                for recipe in sorted(recipes.keys()):
                    surround_print("Help menu for: " + recipe)
                    recipes[recipe].help()
            else:
                for recipe in args[1:]:
                    surround_print("Help menu for: " + recipe)
                    if recipe not in recipes:
                        recipe_obj = load_recipe(recipe)
                        if recipe_obj is not None:
                            print(f"Unknown recipe: {recipe}")
                    else:
                        recipes[recipe].help()
        elif args[0] == "action":
            if len(args) == 1:
                print("Help for all loaded actions:")
                for action in sorted(actions, key=lambda a: a.subname + a.name):
                    surround_print("Help menu for: " + action.name)
                    action.help()
            else:
                for action in args[1:]:
                    possible_actions = list(filter(lambda a: a.subname == action, actions))
                    if len(possible_actions) == 0:
                        return GobiError(self, 1, f"Unknown action: {action}")
                    for action in possible_actions:
                        surround_print("Help menu for: " + action.name)
                        action.help()

class HelpRecipe(Recipe):
    def __init__(self):
        self.name = "help"

    def create_actions(self, gobi_file: GobiFile) -> GobiError | list[Action]:
        return [HelpAction()]


def create() -> Recipe:
    return HelpRecipe()
