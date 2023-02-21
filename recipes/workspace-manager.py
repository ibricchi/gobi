import os
import argparse
from jsonschema import validate
import shutil

from utils.containers import State, Recipe, Action
from utils.logger import Logger

class WorkspaceDirectoryAction(Action):
    dir: str

    def __init__(self, dir: str) -> None:
        super().__init__()
        self.dir = os.path.join(dir)
    
    def run(self) -> None:
        print(self.dir)

class WorkspaceCleanAction(Action):
    dir: str

    def __init__(self, dir: str) -> None:
        super().__init__()
        self.dir = os.path.join(dir)
    
    def run(self, state: State) -> None:
        user_confirmation = input(f"Are you sure you want to delete {self.dir}? [yes/no] ")
        if user_confirmation == "yes":
            shutil.rmtree(self.dir)
        else:
            Logger.fatal(f"[Action {self.name}] Aborting deletion of {self.dir}")

class WorkspaceManager(Recipe):
    tag: str
    base_workspace_dir: str

    def __init__(self, state: State) -> None:
        base_workspace_dir = os.path.join(state.env.config_folder, "workspace-manager")
        for project in state.project_breadcrumbs[1:]:
            base_workspace_dir = os.path.join(base_workspace_dir, project.name)

        self.base_workspace_dir = base_workspace_dir
        
        if not os.path.isdir(self.base_workspace_dir):
            os.makedirs(self.base_workspace_dir)

    def validate(self, config: dict, state: State) -> None:
        if "tag-manager" not in state.context:
            Logger.fatal(f"[Recipe {self.name}] Recipe tag-manager is required for workspace-manager")
        self.tag = state.context["tag-manager"]["tag"]

        if not os.path.isdir(os.path.join(self.base_workspace_dir, self.tag)):
            os.makedirs(os.path.join(self.base_workspace_dir, self.tag))
        
        os.environ["GOBI_WORKSPACE_MANAGER_DIR"] = os.path.join(self.base_workspace_dir, self.tag)

    def register_actions(self, config: dict, state: State) -> list[tuple[str, Action]]:
        return [
            ("wm-dir", WorkspaceDirectoryAction(os.path.join(self.base_workspace_dir, self.tag))),
            ("wm-clean", WorkspaceCleanAction(os.path.join(self.base_workspace_dir, self.tag))),
        ]
    

def create(state: State) -> Recipe:
    return WorkspaceManager(state)