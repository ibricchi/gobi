import os
import subprocess as sp
from jsonschema import validate

from utils.recipe import Recipe
from utils.state import State
from utils.action import Action


class TriggerAction(Action):
    state: State
    actions: list[str]

    def __init__(self, state: State, actions: list[str]) -> None:
        self.state = state
        self.actions = actions

    def run(self) -> None:
        for action in self.actions:
            self.state.actions[action].run()


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
    },
}


class Trigger(Recipe):
    state: State
    actions: dict[str, list[str]]

    def __init__(self, state: State) -> None:
        self.state = state
        self.actions = {}

        validate(instance=state.project_config.config, schema=trigger_schema)

        if "trigger" in state.project_config.config:
            for action_name, action_config in state.project_config["trigger"].items():
                self.state.register_action(
                    action_name, TriggerAction(state, action_config["actions"])
                )
                self.actions[action_name] = action_config["actions"]
    
    def pre_action(self) -> None:
        if self.state.action in self.actions:
            trigger_actions = self.actions[self.state.action]
            for action_name in trigger_actions:
                if action_name not in self.state.actions:
                    print(f"TRIGGER: Action {action_name} does not exist")
                    exit(1)


def create(state: State) -> Recipe:
    return Trigger(state)
