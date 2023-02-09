import os
import subprocess as sp
from jsonschema import validate

from utils.recipe import Recipe
from utils.state import State
from utils.action import Action


class BashAction(Action):
    cwd: str
    command: str
    environment: dict[str, str]
    shell: str

    def __init__(
        self, cwd: str, command: str, environment: dict[str, str], shell: str
    ) -> None:
        self.cwd = cwd
        self.command = command
        self.environment = environment
        self.shell = shell

    def run(self) -> None:
        cwd = os.path.expandvars(os.path.expanduser(self.cwd))
        command = self.command
        environment = {}
        for key, value in self.environment.items():
            new_value = os.path.expandvars(value)
            environment[key] = new_value
        shell = self.shell

        new_env = os.environ.copy() | environment

        sp.run(command, cwd=cwd, shell=True, env=new_env, executable=shell)


bash_schema = {
    "type": "object",
    "properties": {
        "bash": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "cwd": {"type": "string"},
                        "command": {"type": "string"},
                        "shell": {"type": "string"},
                        "env": {
                            "type": "object",
                            "patternProperties": {".*": {"type": "string"}},
                        },
                    },
                    "required": ["cwd", "command"],
                },
            },
            "minProperties": 1,
        },
    },
}


class Bash(Recipe):
    state: State

    def __init__(self, state: State) -> None:
        self.state = state

        validate(instance=state.project_config.config, schema=bash_schema)

        if "bash" in state.project_config.config:
            for action_name, action_config in state.project_config["bash"].items():
                self.state.register_action(action_name, BashAction(
                    cwd=action_config["cwd"],
                    command=action_config["command"],
                    environment=action_config.get("env", {}),
                    shell=action_config.get("shell", "/bin/bash"),
                ))


def create(state: State) -> Recipe:
    return Bash(state)
