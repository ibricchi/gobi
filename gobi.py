#!/usr/bin/env python3

from __future__ import annotations
import sys

from utils.config import Environment, GlobalConfig
from utils.state import State
from utils.recipe import load_recipes
from utils.help import help_menu

if __name__ == "__main__":
    state = State()

    # get project and optional action from command line by parsing the arguments
    # gobi <project> <action>? <args>?
    if len(sys.argv) < 2:
        help_menu()
    
    env = Environment.default()
    state.set("env", env)

    global_config = GlobalConfig(env)
    state.set("global_config", global_config)

    if sys.argv[1] in state.commands:
        state.set("command", sys.argv[1])
        state.set("args", sys.argv[2:] if len(sys.argv) > 2 else [])
        state.commands[state.command].run()
    else:
        state.set("project", sys.argv[1])
        state.set("action", sys.argv[2] if len(sys.argv) > 2 else None)
        state.set("args", sys.argv[3:] if len(sys.argv) > 3 else [])

        project_config = global_config.get_project(state.project)
        state.set("project_config", project_config)

        recipes = load_recipes(state)
        state.set("recipes", recipes)

        if not state.action in state.actions:
            print(f"Action '{state.action}' not found in project '{state.project}'")
            exit(1)

        for recipe in recipes:
            recipe.pre_action()
        
        state.actions[state.action].run()

        for recipe in recipes:
            recipe.post_action()