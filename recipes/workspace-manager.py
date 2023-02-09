import os
import argparse
from jsonschema import validate

from utils.recipe import Recipe
from utils.state import State
from utils.action import Action

class WorkspaceAction(Action):
    dir: str

    def __init__(self, state: State, tag: str) -> None:
        self.dir = os.path.join(state.env.config_folder, "workspace", state.project_config.name, tag)
    
    def run(self) -> None:
        print(self.dir)

class WorkspaceManager(Recipe):
    state: State
    base_workspace_dir: str
    args: argparse.Namespace
    def __init__(self, state: State) -> None:
        self.state = state
        self.base_workspace_dir = os.path.join(state.env.config_folder, "workspace")

        parser = argparse.ArgumentParser()
        parser.add_argument("-t", "--tag")
        parser.add_argument("--workspace-manager-tag")

        args, _ = parser.parse_known_args(state.args)
        self.args = args

        if args.workspace_manager_tag is not None:
            self.tag = args.workspace_manager_tag
        elif args.tag is not None:
            self.tag = args.tag
        else:
            self.tag = "default"
        
        self.state.register_action("workspace", WorkspaceAction(self.state, self.tag))

    def pre_action(self) -> None:
        project_name = self.state.project_config.name
        project_workspace_dir = os.path.join(self.base_workspace_dir, project_name, self.tag)

        if not os.path.isdir(project_workspace_dir):
            os.makedirs(project_workspace_dir)
        
        os.environ["GOBI_WORKSPACE_DIR"] = project_workspace_dir

def create(state: State) -> Recipe:
    return WorkspaceManager(state)