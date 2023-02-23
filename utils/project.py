from future import __annotations__

import os
import sys
import importlib

import tomli
from jsonschema import validate

from .containers import State, Project, Recipe, Action
from .logger import Logger
from .recipe import load_recipe

class ProjectAction(Action):
    project_name: str
    project_path: str

    def __init__(self, project_name: str, project_path: str) -> None:
        super().__init__()
        self.project_name = project_name
        self.project_path = project_path
    
    def run(self, state: State) -> None:
        run_project(self.project_name, self.project_path, state)

project_schema = {
    "type": "object",
    "properties": {
        "gobi": {
            "type": "object",
            "properties": {
                "projects": {
                    "type": "object",
                    "patternProperties": {
                        ".*": { "type": "string" }
                    },
                },
                "recipes": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "child-recipes": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
        },
    },
    "allowUnknown": True,
}

def load_project_config(name: str, config_path: str, state: State) -> Project:
    with open(config_path, 'rb') as f:
        config = tomli.load(f)
    
    validate(config, project_schema)
    
    return Project(name, config_path, config)

def load_project_recipes(project: Project, state: State) -> None:
    for recipe_name in state.child_recipes:
        recipe = load_recipe(recipe_name, state)
        recipe.name = recipe_name
        project.recipes.append(recipe)

    if "gobi" in project.config:
        if "projects" in project.config["gobi"]:
            project.projects = project.config["gobi"]["projects"]
            for project_name, project_path in project.projects.items():
                if not os.path.exists(project_path):
                    Logger.warn(f"[Project {project_name}] In project list, project {project_name} has path {project_path} which does not exist")
                    continue
                if project_name in project.actions:
                    Logger.warn(f"[Project '{project.name}'] Action '{project_name}' already registered by {project.actions[project_name].recipe}")
                    Logger.warn(f"[Project '{project.name}'] Will not register action '{project_name}' from {project.name}")
                    continue
                project.actions[project_name] = ProjectAction(project_name, project_path)
                project.actions[project_name].recipe = project.name
        
        if "recipes" in project.config["gobi"]:
            for recipe_name in project.config["gobi"]["recipes"]:
                if recipe_name in state.child_recipes:
                    Logger.warn(f"[Project '{project.name}'] Recipe '{recipe_name}' is already registered as a child recipe by a parent project")
                    continue
                recipe = load_recipe(recipe_name, state)
                recipe.name = recipe_name
                project.recipes.append(recipe)

        if "child-recipes" in project.config["gobi"]:
            for recipe_name in project.config["gobi"]["child-recipes"]:
                state.child_recipes.append(recipe_name)

def run_project(name: str, path: str, state: State) -> None:
    if len(state.args) == 0:
        Logger.warn(f"[Project '{name}'] No action specified")
        return

    project: Project = load_project_config(name, path, state)
    state.set_project(project)
    load_project_recipes(project, state)
    
    for recipe in project.recipes:
        recipe.validate(project.config, state)
    
    for recipe in project.recipes:
        actions = recipe.register_actions(project.config, state)
        for action_name, action in actions:
            if action_name in project.actions:
                Logger.warn(f"[Project '{project.name}'] Action '{action_name}' already registered by {project.actions[action_name].recipe}")
                Logger.warn(f"[Project '{project.name}'] Will not register action '{action_name}' from {recipe.name}")
                continue

            action.name = action_name
            action.recipe = recipe.name
            project.actions[action_name] = action

    action_name: str = state.args.pop(0)
    if action_name not in project.actions.keys():
        Logger.fatal(f"[Project '{name}'] Unknown action '{action_name}'")

    for recipe in project.recipes:
        recipe.register_hooks(project.config, project.actions, state)
    
    actions_to_run = [project.actions[action_name]]

    while len(actions_to_run) > 0:
        action = actions_to_run.pop(0)
        action.run(state)
        actions_to_run.extend(action.hooks)

    state.unset_project()
