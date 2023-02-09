import os
import argparse

from utils.tools import Tool
from utils.state import State

class BinaryManager(Tool):
    state: State
    base_binary_dir: str
    def __init__(self, state: State) -> None:
        self.state = state
        self.base_binary_dir = os.path.join(state.env.config_folder, "binaries")

        parser = argparse.ArgumentParser()
        parser.add_argument("--version")
        parser.add_argument("--binary-manager-version")

        args, _ = parser.parse_known_args(state.args)
        self.args = args

        if args.binary_manager_version is not None:
            self.version = args.binary_manager_version
        elif args.version is not None:
            self.version = args.version
        else:
            self.version = "default"

    def run_after_recipe_run(self) -> None:
        binary_map = {}
        # check if action has binary-manger set to true
        if "binary-manager" in self.state.action_config.config:
            binary_map = self.state.action_config.config["binary-manager"]
            # check binary_map type
            if not isinstance(binary_map, dict):
                print("binary-manager expects mapping of binary-path to binary-name")
                exit(1)
            for key, value in binary_map.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    print("binary-manager expects mapping of binary-path to binary-name")
                    exit(1)

            binary_map = binary_map
        else:
            return

        project_name = self.state.project_config.name
        project_binary_dir = os.path.join(self.base_binary_dir, project_name)

        if not os.path.isdir(project_binary_dir):
            os.makedirs(project_binary_dir)
        
        for source, target in binary_map.items():
            # expand environment variables in source and target
            source = os.path.expandvars(source)
            target = os.path.expandvars(target)
            if not os.path.isfile(source):
                print(f"WARNING: binary-manager: binary {source} does not exist")
                continue
            
            # make soft link from source to target
            main_path = os.path.join(project_binary_dir, target)
            target_path = os.path.join(project_binary_dir, f"{target}-{self.version}")
            
            if os.path.isfile(target_path) or os.path.islink(target_path):
                os.remove(target_path)

            if os.path.isfile(main_path) or os.path.islink(main_path):
                os.remove(main_path)
            else:
                # print what main_path is
                print(main_path)

            os.symlink(source, target_path)
            os.symlink(target_path, main_path)

def create(state: State) -> Tool:
    return BinaryManager(state)