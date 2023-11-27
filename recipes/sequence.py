from __future__ import annotations

from dataclasses import dataclass

from utils.loader import GobiFile
from utils.recipes import GobiError, Action, Recipe


@dataclass(init=True)
class SequenceConfig:
    subactions: list[str]
    allow_fail: bool


class SequenceAction(Action):
    def __init__(self, name: str, config: SequenceConfig) -> None:
        self.name = "sequence." + name
        self.subname = name
        self.config = config

    def run(
        self,
        gobi_file: GobiFile,
        recipes: dict[str, Recipe],
        actions: list[Action],
        args: list[str],
    ) -> GobiError | None:
        actions_to_run: list[Action] = []
        for action in self.config.subactions:
            possible_actions = list(filter(lambda a: a.subname == action, actions))
            match possible_actions:
                case []:
                    possible_actions = list(filter(lambda a: a.name == action, actions))
                    match possible_actions:
                        case []:
                            return GobiError(self, 1, f"Unknown action: {action}")
                        case [possible_action]:
                            actions_to_run.append(possible_action)
                        case _:
                            return GobiError(self, 1, f"INTERNAL ERROR: Action {action} is ambiguous")
                case [possible_action]:
                    actions_to_run.append(possible_action)
                case _:
                    return GobiError(self, 1, f"Action {action} is ambiguous")

        errors = []
        for action in actions_to_run:
            res = action.run(gobi_file, recipes, actions, [])
            if self.config.allow_fail and res is not None:
                errors.append(res)
            elif res is not None:
                return GobiError(
                    self, res.code, f"Action {res.source.name} failed with msg:\n  {res.msg}"
                )
        if len(errors) == 1:
            return GobiError(
                self,
                errors[0].code,
                f"Action {res.source.name} failed with msg:\n  {errors[0].msg}",
            )
        elif len(errors) > 1:
            return GobiError(
                self,
                1,
                "Multiple actions failed with msgs:\n  {}".format(
                    "\n  ".join(map(lambda e: f"[{e.source.name}] ({e.code}): {e.msg}", errors))
                ),
            )


class SequenceRecipe(Recipe):
    def __init__(self):
        self.name = "sequence"

    def create_actions(self, gobi_file: GobiFile) -> GobiError | list[Action]:
        data = gobi_file.data.get("sequence", {})

        actions = []
        for action, action_data in data.items():
            sub_actions = action_data.get("subactions", [])
            allow_fail = action_data.get("allow_fail", False)
            config = SequenceConfig(sub_actions, allow_fail)
            actions.append(SequenceAction(action, config))
            
        return actions


def create() -> Recipe:
    return SequenceRecipe()
