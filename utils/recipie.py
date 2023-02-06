import os
import sys

from .config import Environment, GlobalConfig, ProjectConfig, ActionConfig

class Recipie:
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def run(self) -> None:
        raise NotImplementedError()

def load_recipie(env: Environment, global_config: GlobalConfig, project_config: ProjectConfig, action_config: ActionConfig, extra_args: list[str]) -> Recipie:
    recipie  = action_config.recipie
    recipie_path = os.path.join(env.recipie_folder, f"{recipie}.py")

    if not os.path.isfile(recipie_path):
        print(f"Recipie {recipie} is required by {action_config.name} {project_config.name} is not installed.")
        print(f"please add it to {env.recipie_folder}")
        exit(1)
    
    # load recipie path
    sys.path.append(env.recipie_folder)
    recipie_module = __import__(recipie)

    # check module includes a function called create
    if not hasattr(recipie_module, "create"):
        print(f"Implementation of recipie {recipie} is missing a create function.")
        exit(1)
    
    # check type of create function is callable and has type:
    # (env: Environment, global_config: GlobalConfig, project_config: ProjectConfig, action_config: ActionConfig) -> Recipie
    create = recipie_module.create
    if not callable(create):
        print(f"Create provided by {recipie} is not callable.")
        exit(1)
    if create.__annotations__ != {
        "env": Environment,
        "global_config": GlobalConfig,
        "project_config": ProjectConfig,
        "action_config": ActionConfig,
        "extra_args": list[str],
        "return": Recipie
    }:
        print(f"Create provided by {recipie} is not of the correct type.")
        exit(1)
    
    # call create function
    return create(env, global_config, project_config, action_config, extra_args)
