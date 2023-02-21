import os
import subprocess as sp
from jsonschema import validate

from utils.containers import State, Recipe, Action
from utils.logger import Logger


class BashAction(Action):
    cwd: str
    command: str
    environment: dict[str, str]
    shell: str

    def __init__(
        self, cwd: str, command: str, environment: dict[str, str], shell: str
    ) -> None:
        super().__init__()
        self.cwd = cwd
        self.command = command
        self.environment = environment
        self.shell = shell

    def run(self, state: State) -> None:
        new_env = os.environ.copy() | self.environment

        sp.run(self.command, cwd=self.cwd, shell=True, env=new_env, executable=self.shell)


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
                        "var_expand_cwd": {"type": "boolean"},
                        "usr_expand_cwd": {"type": "boolean"},
                        "command": {"type": "string"},
                        "shell": {"type": "string"},
                        "var_expand_env_keys": {"type": "boolean"},
                        "env": {
                            "type": "object",
                            "patternProperties": {".*": {"type": "string"}},
                        },
                        "eval_env": {
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
    def validate(self, config: dict, state: State) -> None:
        validate(instance=config, schema=bash_schema)

    def register_actions(self, config: dict, state: State) -> list[tuple[str, Action]]:
        if "bash" in config:
            for name, config in config["bash"].items():
                cwd = config["cwd"]
                var_expand_cwd = config["var_expand_cwd"] if "var_expand_cwd" in config else True
                if var_expand_cwd:
                    cwd = os.path.expandvars(cwd)
                usr_expand_cwd = config["usr_expand_cwd"] if "usr_expand_cwd" in config else True
                if usr_expand_cwd:
                    cwd = os.path.expanduser(cwd)
                command = config["command"]
                shell = config["shell"] if "shell" in config else "/bin/bash"
                var_expand_env_keys = (
                    config["var_expand_env_keys"]
                    if "var_expand_env_keys" in config
                    else True
                )
                environment = {}
                if "env" in config:
                    for key, value in config["env"].items():
                        if var_expand_env_keys:
                            key = os.path.expandvars(key)
                        environment[key] = value
                if "eval_env" in config:
                    for key, value in config["eval_env"].items():
                        if var_expand_env_keys:
                            key = os.path.expandvars(key)
                        run_env = os.environ.copy() | environment
                        environment[key] = sp.run(
                            value,
                            shell=True,
                            capture_output=True,
                            text=True,
                            env=run_env,
                        ).stdout.strip()
                action = BashAction(cwd, command, environment, shell)
                yield (name, action)


def create(state: State) -> Recipe:
    return Bash()
