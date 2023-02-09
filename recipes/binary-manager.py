import os
import argparse
from jsonschema import validate

from utils.recipe import Recipe
from utils.state import State

binary_manager_schema = {
    "type": "object",
    "properties": {
        "binary-manager": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {
                            "type": "string",
                        },
                    },
                    "minProperties": 1,
                },
            },
            "minProperties": 1,
        },
    },
    "required": ["binary-manager"],
}


class BinaryManager(Recipe):
    state: State
    base_binary_dir: str

    def __init__(self, state: State) -> None:
        self.state = state
        self.base_binary_dir = os.path.join(state.env.config_folder, "binaries")

        parser = argparse.ArgumentParser()
        parser.add_argument("-t", "--tag")
        parser.add_argument("--binary-manager-tag")

        args, _ = parser.parse_known_args(state.args)
        self.args = args

        if args.binary_manager_tag is not None:
            self.tag = args.binary_manager_tag
        elif args.tag is not None:
            self.tag = args.tag
        else:
            self.tag = "default"

        validate(
            instance=self.state.project_config.config, schema=binary_manager_schema
        )

    def post_action(self) -> None:
        action_binary_map = self.state.project_config.config["binary-manager"]
        action_name = self.state.action
        if action_name in action_binary_map:
            binary_map = action_binary_map[action_name]

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
                target_path = os.path.join(project_binary_dir, f"{target}-{self.tag}")

                if os.path.isfile(target_path) or os.path.islink(target_path):
                    os.remove(target_path)

                if os.path.isfile(main_path) or os.path.islink(main_path):
                    os.remove(main_path)
                else:
                    # print what main_path is
                    print(main_path)

                os.symlink(source, target_path)
                os.symlink(target_path, main_path)


def create(state: State) -> Recipe:
    return BinaryManager(state)
