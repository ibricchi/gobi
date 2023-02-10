from __future__ import annotations
import os
import sys

from .state import State
from .recipe import Recipe
from .command import Command

def load_recipes(state: State) -> list[Recipe]:
    missing_recipies = []
    for recipe in state.project_config.recipes:
        recipe_path = os.path.join(state.env.recipe_folder, f"{recipe}.py")
        if not os.path.isfile(recipe_path):
            missing_recipies.append(recipe)
    
    if len(missing_recipies) > 0:
        print(f"Recipes {', '.join(missing_recipies)} are required by {state.project_config.name} are not installed.")
        print(f"please add them to {state.env.recipe_folder}")
        exit(1)
    
    recipies_creates = []
    missing_create = []
    non_callables = []
    wrong_type = []
    sys.path.append(state.env.recipe_folder)
    for recipe in state.project_config.recipes:
        recipe_module = __import__(recipe)

        if not hasattr(recipe_module, "create"):
            missing_create.append(recipe)
            continue
    
        create = recipe_module.create
        if not callable(create):
            non_callables.append(recipe)
            continue
        
        if create.__annotations__ != {
                "state": State,
                "return": Recipe
            }:
            wrong_type.append(recipe)
            continue
        
        recipies_creates.append(create)
    
    bad_create = False
    if len(missing_create) > 0:
        print(f"Recipes {', '.join(missing_create)} are missing a create function")
        bad_create = True
    if len(non_callables) > 0:
        print(f"Recipes {', '.join(non_callables)} have a create function that is not callable")
        bad_create = True
    if len(wrong_type) > 0:
        print(f"Recipes {', '.join(wrong_type)} have a create function that does not have the correct type")
        bad_create = True
    if bad_create:
        exit(1)

    return [create(state) for create in recipies_creates]


def load_commands(state: State) -> None:
    missing_commands = []
    for command in state.global_config.commands:
        command_path = os.path.join(state.env.command_folder, f"{command}.py")
        if not os.path.isfile(command_path):
            missing_commands.append(command)
    
    if len(missing_commands) > 0:
        print(f"Commands {', '.join(missing_commands)} are required but not installed.")
        print(f"please add them to {state.env.command_folder}")
        exit(1)
    
    recipies_creates = []
    missing_create = []
    non_callables = []
    wrong_type = []
    sys.path.append(state.env.command_folder)
    for command in state.global_config.commands:
        recipe_module = __import__(command)

        if not hasattr(recipe_module, "create"):
            missing_create.append(command)
            continue
    
        create = recipe_module.create
        if not callable(create):
            non_callables.append(command)
            continue
        
        if create.__annotations__ != {
                "state": State,
                "return": Command
            }:
            wrong_type.append(command)
            continue
        
        recipies_creates.append(create)
    
    bad_create = False
    if len(missing_create) > 0:
        print(f"Recipes {', '.join(missing_create)} are missing a create function")
        bad_create = True
    if len(non_callables) > 0:
        print(f"Recipes {', '.join(non_callables)} have a create function that is not callable")
        bad_create = True
    if len(wrong_type) > 0:
        print(f"Recipes {', '.join(wrong_type)} have a create function that does not have the correct type")
        bad_create = True
    if bad_create:
        exit(1)

    for name, create in zip(state.global_config.commands, recipies_creates):
        state.register_command(name, create(state))