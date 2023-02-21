import os
import argparse
from jsonschema import validate
import subprocess as sp

from utils.containers import State, Recipe, Action
from utils.logger import Logger

tag_manager_schema = {
    "type": "object",
    "properties": {
        "tag-manager": {
            "type": "object",
            "properties": {
                "git": {
                    "type": "object",
                    "properties": {
                        "mode": {"type": "string"},
                        "dir": {"type": "string"},
                    },
                    "required": ["mode", "dir"],
                },
            },
            "minProperties": 1,
            "maxProperties": 1,
        },
    },
}

class TagManager(Recipe):
    tag: str

    def __init__(self, state: State) -> None:
        self.state = state
        
        # TODO: figure out a better way of handling that this
        # recipe needs to set state ahead of other recipies
        validate(instance=state.project.config, schema=tag_manager_schema)

        if "tag-manager" in state.project.config:
            if "git" in state.project.config["tag-manager"]:
                git_config = state.project.config["tag-manager"]["git"]
                dir = os.path.expanduser(os.path.expandvars(git_config["dir"]))
                if git_config["mode"] == "branch":
                    self.tag = sp.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=dir).decode("utf-8").strip()
                elif git_config["mode"] == "commit":
                    self.tag = sp.check_output(["git", "rev-parse", "HEAD"], cwd=git_config["dir"]).decode("utf-8").strip()
                else:
                    Logger.fatal("Invalid tag-manager configuration")
            else:
                Logger.fatal("Invalid tag-manager configuration")
        else:
            if "-t" in state.args:
                arg_idx = state.args.index("-t")
                self.tag = state.args[arg_idx + 1]
            elif "--tag" in state.args:
                arg_idx = state.args.index("--tag")
                self.tag = state.args[arg_idx + 1]
            else:
                self.tag = "default"
        
        state.context["tag-manager"] = {}
        state.context["tag-manager"]["tag"] = self.tag

        os.environ["GOBI_TAG_MANAGER_TAG"] = self.tag


def create(state: State) -> Recipe:
    return TagManager(state)
