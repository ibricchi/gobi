from __future__ import annotations
from re import sub

from utils.loader import GobiFile
from utils.recipes import GobiError, Action, Recipe


class ListAction(Action):
    def __init__(self) -> None:
        super().__init__()
        self.name = "list"
        self.subname = "list"

    def help(self) -> str:
        return """
Get a list of all available actions for a project
Usage: gobi <project list...>? list [porcelain|full]

By default will try and display the subname of available actions unless a conflict exists, then will use the full name.
Porcelain will not print out the message at the start of the list command.
Full will print out the full name of all actions.
"""

    @staticmethod
    def print_list(actions: list[Action], full: bool = False) -> None:
        if full:
            for action in sorted(actions, key=lambda a: a.subname):
                print(action.name)
        else:
            minimal_name: dict[str, list[Action]] = {}
            for action in actions:
                if action.subname not in minimal_name:
                    minimal_name[action.subname] = [action]
                else:
                    minimal_name[action.subname].append(action)
            sorted_subnames = sorted(minimal_name.keys())
            for subname in sorted_subnames:
                actions = minimal_name[subname]
                priority_actions = [a for a in actions if a.priority]
                if len(priority_actions) == 1:
                    print(subname)
                elif len(priority_actions) > 1:
                    for a in sorted(priority_actions, key=lambda a: a.name):
                        print(a.name)
                elif len(actions) == 1:
                    print(subname)
                else:
                    for a in sorted(actions, key=lambda a: a.name):
                        print(a.name)

    def run(
        self,
        gobi_file: GobiFile,
        recipes: dict[str, Recipe],
        actions: list[Action],
        args: list[str],
    ) -> GobiError | None:
        match args:
            case []:
                print("List of available actions:")
                ListAction.print_list(actions)
            case ["porcelain"]:
                ListAction.print_list(actions)
            case ["full"]:
                ListAction.print_list(actions, full=True)
            case [arg]:
                return GobiError(self, 1, f"Unknown argument: {arg}")
            case _:
                return GobiError(self, 1, "Too many arguments passed to list action")


class ListRecipe(Recipe):
    def __init__(self):
        self.name = "list"

    def help(self) -> str:
        return "Generates the list action for gobi."

    def create_actions(self, gobi_file: GobiFile) -> GobiError | tuple[list[Action], list[str]]:
        return [ListAction()], []


def create() -> Recipe:
    return ListRecipe()
