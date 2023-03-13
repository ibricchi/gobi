import os
import subprocess as sp
from jsonschema import validate
import tomli_w

from utils.containers import State, Recipe, Action
from utils.logger import Logger


class RegisterAction(Action):
    project_config: dict
    def __init__(self, project_config: dict) -> None:
        super().__init__()
        self.project_config = project_config

    def run(self, state: State) -> None:
        if len(state.args) < 2:
            Logger.fatal(f"[Action {self.name}] Registering a new project requires a name and a path")
        
        name = state.args[0]
        path = os.path.realpath(state.args[1])
        
        if "gobi" not in self.project_config:
            self.project_config["gobi"] = {}
        
        if "projects" not in self.project_config["gobi"]:
            self.project_config["gobi"]["projects"] = {}

        # check if the project already exists
        if name in self.project_config["gobi"]["projects"]:
            Logger.warn(f"[Action {self.name}] Project {name} already exists with path {self.project_config['gobi']['projects'][name]}")
            Logger.warn(f"[Action {self.name}] Will not register project {name} with path {path}")
            Logger.warn(f"[Action {self.name}] To update the path, use the 'update' action")
            return
        
        # check if the path exists
        if not os.path.exists(path):
            Logger.warn(f"[Action {self.name}] Path {path} does not exist")
            Logger.warn(f"[Action {self.name}] Will not register project {name} with path {path}")
            return
        
        self.project_config["gobi"]["projects"][name] = path

        # write the config
        with open(state.project.config_path, "wb") as f:
            tomli_w.dump(self.project_config, f)

class UpdateAction(Action):
    project_config: dict
    def __init__(self, project_config: dict) -> None:
        super().__init__()
        self.project_config = project_config
    
    def run(self, state: State) -> None:
        if len(state.args) < 2:
            Logger.fatal(f"[Action {self.name}] Updating a project requires a name and a path")
        
        name = state.args[0]
        path = os.path.realpath(state.args[1])
        
        # check if the project exists
        if name not in self.project_config["gobi"]["projects"]:
            Logger.warn(f"[Action {self.name}] Project {name} does not exist")
            Logger.warn(f"[Action {self.name}] Will not update project {name} with path {path}")
            return
        
        # check if the path exists
        if not os.path.exists(path):
            Logger.warn(f"[Action {self.name}] Path {path} does not exist")
            Logger.warn(f"[Action {self.name}] Will not update project {name} with path {path}")
            return
        
        self.project_config["gobi"]["projects"][name] = path

        # write the config
        with open(state.project.config_path, "wb") as f:
            tomli_w.dump(self.project_config, f)

class RemoveAction(Action):
    project_config: dict
    def __init__(self, project_config: dict) -> None:
        super().__init__()
        self.project_config = project_config
    
    def run(self, state: State) -> None:
        if len(state.args) < 1:
            Logger.fatal(f"[Action {self.name}] Removing a project requires a name")
        
        name = state.args[0]
        
        if "gobi" not in self.project_config:
            self.project_config["gobi"] = {}
        
        if "projects" not in self.project_config["gobi"]:
            self.project_config["gobi"]["projects"] = {}

        # check if the project exists
        if name not in self.project_config["gobi"]["projects"]:
            Logger.warn(f"[Action {self.name}] Project {name} does not exist")
            Logger.warn(f"[Action {self.name}] Will not remove project {name}")
            return
        
        del self.project_config["gobi"]["projects"][name]

        # write the config
        with open(state.project.config_path, "wb") as f:
            tomli_w.dump(self.project_config, f)

class WhereAction(Action):
    def run(self, state: State) -> None:
        if len(state.args) < 1:
            Logger.fatal(f"[Action {self.name}] Finding a project requires a name")
        
        name = state.args[0]
        
        # check if the project exists
        if name not in state.project.config["gobi"]["projects"]:
            Logger.warn(f"[Action {self.name}] Project {name} does not exist")
            Logger.warn(f"[Action {self.name}] Will not find project {name}")
            return
        
        print(state.project.config['gobi']['projects'][name])

class ProjectManagerRecipe(Recipe):    
    def register_actions(self, config: dict, state: State) -> list[tuple[str, Action]]:
        return [
            ("register", RegisterAction(config)),
            ("update", UpdateAction(config)),
            ("remove", RemoveAction(config)),
            ("where", WhereAction())
        ]


def create(state: State) -> Recipe:
    return ProjectManagerRecipe()
