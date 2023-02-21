import os
import argparse
from jsonschema import validate
import shutil

from utils.containers import State, Recipe, Action
from utils.logger import Logger

class BinaryDirectoryAction(Action):
    dir: str

    def __init__(self, dir: str) -> None:
        super().__init__()
        self.dir = os.path.join(dir)
    
    def run(self, state: State) -> None:
        print(self.dir)

class BinaryCleanAction(Action):
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

class BinaryManagerAction(Action):
    tag: str
    dir: str
    binaries: dict[str, str]
    link_main: bool

    def __init__(self, tag, dir: str, binaries: dict[str, str], link_main: bool) -> None:
        super().__init__()
        self.tag = tag
        self.dir = dir
        self.binaries = binaries
        self.link_main = link_main
    
    def run(self, state: State) -> None:
        for name, path in self.binaries.items():
            path = os.path.expanduser(os.path.expandvars(path))
            if not os.path.exists(path):
                Logger.warn(f"[Action {self.name}] Binary {name} has path {path} which does not exist")
                continue
            if not os.path.isdir(self.dir):
                os.makedirs(self.dir)
            
            if os.path.exists(os.path.join(self.dir,  f"{name}-{self.tag}")):
                os.remove(os.path.join(self.dir,  f"{name}-{self.tag}"))
            os.symlink(path, os.path.join(self.dir, f"{name}-{self.tag}"))

            if self.link_main:
                if os.path.exists(os.path.join(self.dir, name)):
                    os.remove(os.path.join(self.dir, name))
                os.symlink(os.path.join(self.dir, f"{name}-{self.tag}"), os.path.join(self.dir, name))

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
}


class BinaryManager(Recipe):
    tag: str
    link_main: bool
    base_binary_dir: str

    def __init__(self, state: State) -> None:
        self.link_main = True

        base_bianary_dir = os.path.join(state.env.config_folder, "binary-manager")
        for project in state.project_breadcrumbs[1:]:
            base_bianary_dir = os.path.join(base_bianary_dir, project.name)

        self.base_binary_dir = base_bianary_dir
        os.environ["GOBI_BINARY_MANAGER_DIR"] = self.base_binary_dir

    def validate(self, config: dict, state: State) -> None:
        if "tag-manager" not in state.context:
            Logger.fatal(f"[Recipe {self.name}] Recipe tag-manager is required for binary-manager")
        self.tag = state.context["tag-manager"]["tag"]

        if "--binary-manager-no-link" in state.args:
            self.link_main = False
            state.args.pop(state.args.index("--binary-manager-no-link"))

        validate(instance=config, schema=binary_manager_schema)

    def register_actions(self, config: dict, state: State) -> list[tuple[str, Action]]:
        return [
            ("bm-dir", BinaryDirectoryAction(os.path.join(self.base_binary_dir, self.tag))),
            ("bm-clean", BinaryCleanAction(os.path.join(self.base_binary_dir, self.tag)))
        ]

    def register_hooks(self, config: dict, actions: dict[str, Action], state: State) -> None:
        if "binary-manager" in config:
            for action_name, action_config in config["binary-manager"].items():
                if action_name not in actions:
                    Logger.warn(f"[Recipe {self.name}] Action {action_name} does not exist, cannot register binary-manager hooks")
                    continue
                action = BinaryManagerAction(self.tag , self.base_binary_dir, action_config, self.link_main)
                action.name = f"binary-manager-{action_name}-hook"
                actions[action_name].hooks.append(action)

def create(state: State) -> Recipe:
    return BinaryManager(state)
