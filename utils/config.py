from __future__ import annotations
from dataclasses import dataclass
import tomli
import os
from typing import Any

@dataclass(frozen=True)
class Environment:
    config_folder: str
    config_file: str
    recipie_folder: str

    @classmethod
    def default(cls):
        config_folder = os.path.join(os.path.expanduser("~"), ".gobi")
        if os.environ.get("GOBI_CONFIG_FOLDER"):
            config_folder = os.environ.get("GOBI_CONFIG_FOLDER")
            assert config_folder is not None
            # check config folder exists
            if not os.path.isdir(config_folder):
                print("Could not find gobi config folder specified by GOBI_CONFIG_FOLDER environment variable")
                exit(1)
        else:
            if not os.path.isdir(config_folder):
                print("Could not find gobi config folder at default ~/.gobi/, you can override this using GOBI_CONFIG_FOLDER")
                exit(1)
        
        config_file = os.path.join(config_folder, "config.toml")
        if not os.path.isfile(config_file):
            print(f"Could not find gobi config file at expected: '{config_file}'")
            exit(1)

        recipie_folder = os.path.join(config_folder, "recipies")
        if not os.path.isdir(recipie_folder):
            print(f"Could not find gobi recipie folder at expected: '{recipie_folder}'")
        

        return cls(config_folder, config_file, recipie_folder)

class ActionConfig:
    env: Environment
    name: str
    recipie: str
    config: dict[str, Any]

    def __init__(self, env: Environment, action: str, config: dict[str, Any]) -> None:
        self.env = env
        self.config = config
        self.recipie = self.config["recipie"]
        self.name = action

    def __getitem__(self, key):
        return self.config[key]

class ProjectConfig:
    env: Environment
    path: str
    name: str
    actions: dict[str, Any]
    config: dict[str, Any]

    def __init__(self, env: Environment, project: str, project_path: str) -> None:
        self.env = env
        self.path = project_path
        self.name = project

        # check that config path is a file
        if not os.path.isfile(self.path):
            print(f"Specified config file for {project} '{self.path}' not found at {self.path}")
            exit(1)

        with open(self.path, "rb") as f:
            try:
                self.config = tomli.load(f)
            except tomli.TOMLDecodeError as e:
                print(f"Error parsing config file '{self.path}' for {project}: {e}")
                exit(1)

        # check that there is at least one action
        if not "action" in self.config:
            print(f"Config file for {project} '{self.path}' does not contain an 'action' key")
            exit(1)
        if not isinstance(self.config["action"], dict):
            print(
                f"Config file for {project} '{self.path}' has an 'action' key that is not a dictionary"
            )
            exit(1)

        # ensure all actions have a recipie value
        no_recipie_actions = []
        wrong_recipie_type_actions = []
        for _, action in self.config["action"].items():
            if not "recipie" in action:
                no_recipie_actions.append(action)
            elif not isinstance(action["recipie"], str):
                wrong_recipie_type_actions.append(action)
        if len(no_recipie_actions) > 0:
            print(
                f"Config file for {project} '{self.path}' has actions with no recipie: {', '.join(no_recipie_actions)}"
            )
            exit(1)
        if len(wrong_recipie_type_actions) > 0:
            print(
                f"Config file for {project} '{self.path}' has actions with recipie that is not a string: {', '.join(wrong_recipie_type_actions)}"
            )
            exit(1)

        self.actions = self.config["action"]

    def __getitem__(self, key):
        return self.config[key]
    
    def get_action(self, action: str) -> ActionConfig:
        if not action in self.actions:
            print(f"Project {self.name} has no action '{action}'")
            exit(1)
        
        return ActionConfig(self.env, action, self.actions[action])

class GlobalConfig:
    env: Environment
    path: str
    projects: dict[str, str]
    config: dict[str, Any]

    def __init__(self, env: Environment) -> None:
        self.env = env
        self.path = env.config_file

        with open(self.path, "rb") as f:
            try:
                self.config = tomli.load(f)
            except tomli.TOMLDecodeError as e:
                print(f"Error parsing config file '{self.path}': {e}")
                exit(1)

        # check that config has recipies key
        if not "projects" in self.config:
            print(f"Config file '{self.path}' does not contain a 'projects'")
            exit(1)
        if not isinstance(self.config["projects"], dict):
            print(f"Config file '{self.path}' has a 'projects' key that is not a dictionary")
            exit(1)

        # check that all projects are str -> str mappings
        wrong_type_projects = []
        for project in self.config["projects"]:
            if not isinstance(self.config["projects"][project], str):
                wrong_type_projects.append(project)
        if len(wrong_type_projects) > 0:
            print(
                f"Config file '{self.path}' has projects with values that are not strings: {', '.join(wrong_type_projects)}"
            )
            exit(1)
        
        self.projects = self.config["projects"]

    def __getitem__(self, key):
        return self.config[key]
    
    def get_project(self, project: str):
        if not project in self.projects:
            print(f"Project {project} not found in config file '{self.path}'")
            exit(1)

        project_path = self.projects[project]
        return ProjectConfig(self.env, project, project_path)