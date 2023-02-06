import os
import subprocess as sp
from utils.recipie import Recipie
from utils.config import Environment, GlobalConfig, ProjectConfig, ActionConfig

class BashRecipie(Recipie):
    cwd: str
    command: str
    environment: dict[str, str]

    def __init__(self, cwd: str, command: str, environment: dict[str, str]) -> None:
        self.cwd = cwd
        self.command = command
        self.environment = environment

    def run(self) -> None:
        new_env = os.environ.copy() | self.environment
        proc = sp.run(self.command, cwd=self.cwd, shell=True, env=new_env)

def create(env: Environment, global_config: GlobalConfig, project_config: ProjectConfig, action_config: ActionConfig, extra_args: list[str]) -> Recipie:
    # make sure action_config includes the required fields
    required_fields = ["cwd", "command", "env"]
    missed_fields = []
    for field in required_fields:
        if field not in action_config.config:
            missed_fields.append(field)
    if len(missed_fields) > 0:
        print(f"Action {action_config.name} for project {project_config.name} is missing the following fields: {missed_fields}")
        exit(1)

    # make sure action_config filed types are correct
    bad_type = False
    if type(action_config["cwd"]) != str:
        print(f"Action {action_config.name} for project {project_config.name} has an incorrect type for cwd.")
        bad_type = True
    if type(action_config["command"]) != str:
        print(f"Action {action_config.name} for project {project_config.name} has an incorrect type for command.")
        bad_type = True
    if type(action_config["env"]) != dict:
        print(f"Action {action_config.name} for project {project_config.name} has an incorrect type for env.")
        bad_type = True
    else:
        for key, value in action_config["env"].items():
            if type(key) != str or type(value) != str:
                print(f"Action {action_config.name} for project {project_config.name} has an incorrect type for env.")
                bad_type = True
                break
    if bad_type:
        exit(1)

    # expand user in cwd
    cwd = os.path.expanduser(action_config["cwd"])
    # check cwd is valid
    if not os.path.isdir(cwd):
        print(f"Action {action_config.name} for project {project_config.name} has an invalid cwd.")
        exit(1)

    command = action_config["command"]
    environment = action_config["env"]

    return BashRecipie(cwd, command, environment)