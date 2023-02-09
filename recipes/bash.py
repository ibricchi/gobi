import os
import subprocess as sp
from utils.recipe import Recipe
from utils.state import State

class Bashrecipe(Recipe):
    cwd: str
    command: str
    environment: dict[str, str]

    def __init__(self, cwd: str, command: str, environment: dict[str, str]) -> None:
        self.cwd = cwd
        self.command = command
        self.environment = environment

    def run(self) -> None:
        new_env = os.environ.copy() | self.environment
        proc = sp.run(self.command, cwd=self.cwd, shell=True, env=new_env, executable='/bin/bash')

def create(state: State) -> Recipe:
    # make sure action_config includes the required fields
    required_fields = ["cwd", "command"]
    missed_fields = []
    for field in required_fields:
        if field not in state.action_config.config:
            missed_fields.append(field)
    if len(missed_fields) > 0:
        print(f"Action {state.action_config.name} for project {state.project_config.name} is missing the following fields: {missed_fields}")
        exit(1)

    # make sure action_config filed types are correct
    bad_type = False
    if type(state.action_config["cwd"]) != str:
        print(f"Action {state.action_config.name} for project {state.project_config.name} has an incorrect type for cwd.")
        bad_type = True
    if type(state.action_config["command"]) != str:
        print(f"Action {state.action_config.name} for project {state.project_config.name} has an incorrect type for command.")
        bad_type = True
    if "env" in state.action_config.config:
        if type(state.action_config["env"]) != dict:
            print(f"Action {state.action_config.name} for project {state.project_config.name} has an incorrect type for env.")
            bad_type = True
        else:
            for key, value in state.action_config["env"].items():
                if type(key) != str or type(value) != str:
                    print(f"Action {state.action_config.name} for project {state.project_config.name} has an incorrect type for env.")
                    bad_type = True
                    break
    if bad_type:
        exit(1)

    # expand user in cwd
    cwd = os.path.expanduser(state.action_config["cwd"])
    cwd = os.path.expandvars(cwd)

    # check cwd is valid
    if not os.path.isdir(cwd):
        print(f"Action {state.action_config.name} for project {state.project_config.name} has an invalid cwd.")
        exit(1)

    command = state.action_config["command"]
    
    environment = {}
    if "env" in state.action_config.config:
        environment = state.action_config["env"]

    return Bashrecipe(cwd, command, environment)