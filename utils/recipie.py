import os
import sys

from .state import State

class Recipie:
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def run(self) -> None:
        raise NotImplementedError()

def load_recipie(state: State) -> Recipie:
    recipie  = state.action_config.recipie
    recipie_path = os.path.join(state.env.recipie_folder, f"{recipie}.py")

    if not os.path.isfile(recipie_path):
        print(f"Recipie {recipie} is required by {state.action_config.name} {state.project_config.name} is not installed.")
        print(f"please add it to {state.env.recipie_folder}")
        exit(1)
    
    # load recipie path
    sys.path.append(state.env.recipie_folder)
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
        "state": State,
        "return": Recipie
    }:
        print(f"Create provided by {recipie} is not of the correct type.")
        exit(1)
    
    # call create function
    return create(state)
