import os
import subprocess as sp
from jsonschema import validate

from utils.containers import State, Recipe, Action
from utils.logger import Logger

class TriggerAction(Action):
    actions: list[str]

    def __init__(self, actions: list[str]) -> None:
        super().__init__()
        self.actions = actions

    def run(self, state: State) -> None:
        for action in self.actions:
            if action not in state.project.actions:
                Logger.warn(f"[Action {self.name}] Attempting to tigger action {action} which does not exist")
                continue
            state.project.actions[action].run(state)
            self.hooks.extend(state.project.actions[action].hooks)

trigger_schema = {
    "type": "object",
    "properties": {
        "trigger": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "actions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                        }
                    },
                    "required": ["actions"],
                },
            },
            "minProperties": 1,
        },
        "trigger-action": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "actions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                        }
                    },
                    "required": ["actions"],
                },
            },
            "minProperties": 1,
        },
    },
}


class Trigger(Recipe):
    def validate(self, config: dict, state: State) -> None:
        validate(instance=config, schema=trigger_schema)

    def register_actions(self, config: dict, state: State) -> list[tuple[str, Action]]:
        if "trigger-action" in config:
            for action_name, action_config in config["trigger-action"].items():
                action = TriggerAction(action_config["actions"])
                yield (action_name, action)

    def register_hooks(self, config: dict, actions: dict[str, Action], state: State) -> None:
        if "trigger" in config:
            for action_name, action_config in config["trigger"].items():
                if action_name not in actions:
                    Logger.warn(f"[Recipe {self.name}] Action {action_name} does not exist. Cannot register triggers for it.")
                    Logger.warn(f"[Recipe {self.name}] If you are trying to register this action consider labeling it trigger-action instead of trigger")
                    continue
                for trigger_action_name in action_config["actions"]:
                    if trigger_action_name not in actions:
                        Logger.warn(f"[Recipe {self.name}] Action {trigger_action_name} does not exist. Cannot register it to trigger for {action_name}.")
                        continue
                    actions[action_name].hooks.append(actions[trigger_action_name])

def create(state: State) -> Recipe:
    return Trigger()
