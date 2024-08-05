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
        super().__init__()
        self.name = "help"
        self.subname = "help"

    def help(self) -> str:
        return "How clever of you to find this help menu!"

    def help_menu(self) -> None:
        print("""
Usage: gobi <project list...>? help [recipe|action] <recipe name|action name...>?

default: prints this help menu

recipe: prints the help menu for all recipes loaded in the current project
        <recipe name...>: prints the help menu for the specified recipes

action: prints the help menu for all actions loaded in the current project
        <action name...>: prints the help menu for the specified actions
""")

    def run(
        self,
        gobi_file: GobiFile,
        recipes: dict[str, Recipe],
        actions: list[Action],
        args: list[str],
    ) -> GobiError | None:
        if args == []:
            self.help_menu()
        elif args[0] == "recipe":
            if len(args) == 1:
                print("Help for all loaded recipes:\n")
                for recipe in sorted(recipes.keys()):
                    surround_print("Help menu for: " + recipe)
                    print(f"\n{recipes[recipe].help().strip()}\n")
            else:
                for recipe in args[1:]:
                    surround_print("Help menu for: " + recipe)
                    if recipe not in recipes:
                        recipe_obj = load_recipe(recipe)
                        if recipe_obj is not None:
                            print(f"Unknown recipe: {recipe}")
                    else:
                        print(f"\n{recipes[recipe].help().strip()}\n")
        elif args[0] == "action":
            if len(args) == 1:
                print("Help for all loaded actions:")
                for action in sorted(actions, key=lambda a: a.subname + a.name):
                    surround_print("Help menu for: " + action.name)
                    print(f"\n{action.help().strip()}\n")
            else:
                for action in args[1:]:
                    possible_actions = list(filter(lambda a: a.subname == action, actions))
                    if len(possible_actions) == 0:
                        return GobiError(self, 1, f"Unknown action: {action}")
                    for action in possible_actions:
                        surround_print("Help menu for: " + action.name)
                        print(f"\n{action.help().strip()}\n")

class HelpRecipe(Recipe):
    def __init__(self):
        self.name = "help"

    def help(self) -> str:
        return "Generates the help action for gobi."

    def create_actions(self, gobi_file: GobiFile) -> GobiError | list[Action]:
        return [HelpAction()]


def create() -> Recipe:
    return HelpRecipe()
