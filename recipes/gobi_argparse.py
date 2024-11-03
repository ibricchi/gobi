from __future__ import annotations

import argparse
from typing import Type
from pydoc import locate
import os

from utils.loader import GobiFile
from utils.recipes import GobiError, Action, Recipe


class ArgparseAction(Action):
    def __init__(self, name: str, subaction: str, passthrough: bool, ap: argparse.ArgumentParser) -> None:
        super().__init__()
        self.name = "argparse." + name
        self.subname = name
        self.subaction = subaction
        self.passthrough = passthrough
        self.ap = ap

    def help(self) -> str:
        return f"Running action {self.subaction} with args:\n\n{self.ap.format_help()}"

    def run(
        self,
        gobi_file: GobiFile,
        recipes: dict[str, Recipe],
        actions: list[Action],
        args: list[str],
    ) -> GobiError | None:
        parsed_args, unparsed_args = self.ap.parse_known_args(args)
        if not self.passthrough and len(unparsed_args) > 0:
            return GobiError(self, 1, f"Unknown argument: {unparsed_args[0]}\n{self.ap.format_help()}")
        for arg in vars(parsed_args):
            # set as environment variable
            os.environ[f"{arg}"] = str(getattr(parsed_args, arg))
            os.environ[f"GOBI_ARGPARSE_{arg}"] = str(getattr(parsed_args, arg))
        
        action_to_run = None
        possible_actions = list(filter(lambda a: a.subname == self.subaction, actions))
        match possible_actions:
            case []:
                possible_actions = list(filter(lambda a: a.name == self.subaction, actions))
                match possible_actions:
                    case []:
                        return GobiError(self, 1, f"Unknown action: {self.subaction}")
                    case [possible_action]:
                        action_to_run = possible_action
                    case _:
                        return GobiError(self, 1, f"INTERNAL ERROR: Action {self.subaction} is ambiguous")
            case [possible_action]:
                action_to_run = possible_action
            case _:
                return GobiError(self, 1, f"Action {self.subaction} is ambiguous")

        return action_to_run.run(gobi_file, recipes, actions, unparsed_args)

class ArgparseRecipe(Recipe):
    def __init__(self):
        self.name = "argparse"

    def help(self) -> str:
        return """
Generates an argparse wrapper around a given subacton.

This recipe uses the following configuration options:

[argparse.<action name>.subaction] (required) : str
    name of subaction to call

[argparse.<action name>.passthrough] (optional) : bool
    if true, allows unknown arguments to be passed to subaction

Each argument is defined with the following options:
[argparse.<action name>.args.<arg name>] (required) : str
    name of argument

[argparse.<action name>.args.<arg name>.default] (optional) : str
    Default value for argument

[argparse.<action name>.args.<arg name>.help] (optional) : str
    Help text for argument

[argparse.<action name>.args.<arg name>.required] (optional) : bool
    If true, argument is required

[argparse.<action name>.args.<arg name>.choices] (optional) : list[str]
    List of allowed choices

"""

    def create_actions(self, gobi_file: GobiFile) -> GobiError | tuple[list[Action], list[str]]:
        config = gobi_file.data.get("argparse", {})

        actions: list[Action] = []
        deps: list[str] = []
        for name in config:
            cfg = config.get(name)
            ap = argparse.ArgumentParser(prog=f"gobi <projects> {name}", add_help=False)

            if "subaction" not in cfg:
                return GobiError(self, -1, "Argparse actions require subaction")
            subaction = cfg.get("subaction")

            passthrough = cfg.get("passthrough", False)

            if "args" not in cfg:
                return GobiError(self, -1, "Argparse actions require args")

            args = cfg.get("args", {})
            for aname in args:
                acfg = args.get(aname)
                default = acfg.get("default", None)
                help = acfg.get("help", None)
                required = acfg.get("required", False)

                choises = acfg.get("choices", None)
                short = acfg.get("short", None)

                arg_options = [f"--{aname}"]
                if short is not None:
                    arg_options = [f"-{short}"] + arg_options

                ap.add_argument(
                    *arg_options,
                    default=default,
                    help=help,
                    required=required,
                    choices=choises,
                )
            
            actions.append(ArgparseAction(name,subaction,passthrough,ap))

        return actions, deps


def create() -> Recipe:
    return ArgparseRecipe()
