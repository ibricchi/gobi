import os
import argparse

from utils.tools import Tool
from utils.state import State

class WorkspaceManager(Tool):
    state: State
    base_workspace_dir: str
    args: argparse.Namespace
    def __init__(self, state: State) -> None:
        self.state = state
        self.base_workspace_dir = os.path.join(state.env.config_folder, "workspace")

        parser = argparse.ArgumentParser()
        parser.add_argument("--version")
        parser.add_argument("--workspace-manager-version")

        args, _ = parser.parse_known_args(state.args)
        self.args = args

        if args.workspace_manager_version is not None:
            self.version = args.workspace_manager_version
        elif args.version is not None:
            self.version = args.version
        else:
            self.version = "default"

    def run_before_recipie_load(self) -> None:
        project_name = self.state.project_config.name
        project_workspace_dir = os.path.join(self.base_workspace_dir, project_name, self.version)

        if not os.path.isdir(project_workspace_dir):
            os.makedirs(project_workspace_dir)
        os.environ["GOBI_WORKSPACE_DIR"] = project_workspace_dir

def create(state: State) -> Tool:
    return WorkspaceManager(state)