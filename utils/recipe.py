import os
import sys

from .state import State

class Recipe:
    def run(self) -> None:
        raise NotImplementedError()

def load_recipe(state: State) -> Recipe:
    recipe  = state.action_config.recipe
    recipe_path = os.path.join(state.env.recipe_folder, f"{recipe}.py")

    if not os.path.isfile(recipe_path):
        print(f"recipe {recipe} is required by {state.action_config.name} {state.project_config.name} is not installed.")
        print(f"please add it to {state.env.recipe_folder}")
        exit(1)
    
    # load recipe path
    sys.path.append(state.env.recipe_folder)
    recipe_module = __import__(recipe)

    # check module includes a function called create
    if not hasattr(recipe_module, "create"):
        print(f"Implementation of recipe {recipe} is missing a create function.")
        exit(1)
    
    # check type of create function is callable and has type:
    # (env: Environment, global_config: GlobalConfig, project_config: ProjectConfig, action_config: ActionConfig) -> recipe
    create = recipe_module.create
    if not callable(create):
        print(f"Create provided by {recipe} is not callable.")
        exit(1)
    if create.__annotations__ != {
        "state": State,
        "return": Recipe
    }:
        print(f"Create provided by {recipe} is not of the correct type.")
        exit(1)
    
    # call create function
    return create(state)
