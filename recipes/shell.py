from __future__ import annotations

import os
import shutil
import subprocess as sp
import tempfile as tf

from utils.loader import GobiFile
from utils.recipes import GobiError, Action, Recipe


class ShellConfig:
    shell: str
    params: list[str]
    env: dict[str, str]
    eval_env: dict[str, str]
    cwd: str

    def copy(self) -> ShellConfig:
        new = ShellConfig()
        new.shell = self.shell
        new.params = self.params.copy()
        new.env = self.env.copy()
        new.eval_env = self.eval_env.copy()
        new.cwd = self.cwd
        return new


class ShellAction(Action):
    config: ShellConfig
    command: str

    def __init__(self, name, subname, config, command) -> None:
        self.name = name
        self.subname = subname
        self.config = config
        self.command = command

    def run(
        self,
        gobi_file: GobiFile,
        recipes: dict[str, Recipe],
        actions: dict[str, Action],
        args: list[str],
    ) -> GobiError | None:
        command_base = [self.config.shell] + self.config.params
        
        # make sure shell is a valid executable
        if not shutil.which(self.config.shell):
            return GobiError(self, 1, f"Shell '{self.config.shell}' is not a valid executable")

        # add environ variables
        env = os.environ.copy()

        # add eval env
        for key, value in self.config.eval_env.items():
            command_file = tf.NamedTemporaryFile(
                mode="w",
            )
            with tf.NamedTemporaryFile(mode="w") as command_file:
                command_file.write(value)
                command_file.flush()
                res = sp.run(
                    command_base + [command_file.name],
                    capture_output=True,
                    text=True,
                    env=env,
                )
                if res.returncode != 0:
                    return GobiError(
                        self,
                        res.returncode,
                        "Shell action failed to setup eval envs, failed at " + key,
                    )
                env[key] = res.stdout.strip()

        # add normal env
        env |= self.config.env

        # add args
        for i, arg in enumerate(args):
            env[f"ARG{i}"] = arg

        # run command
        with tf.NamedTemporaryFile(mode="w") as command_file:
            command_file.write(self.command)
            command_file.flush()
            res = sp.run(
                command_base + [command_file.name] + args,
                env=env,
                cwd=self.config.cwd,
            )

        if res.returncode != 0:
            return GobiError(self, res.returncode, "Shell command failed")


class ShellRecipe(Recipe):
    def __init__(self):
        self.name = "shell"

    def create_actions(self, gobi_file: GobiFile) -> GobiError | list[Action]:
        data = gobi_file.data.get("shell", {})

        # first we get the global shell config
        global_data = data.get("gobi", {})
        global_config = ShellConfig()
        global_config.shell = global_data.get("shell", "/bin/sh")
        global_config.params = global_data.get("params", [])
        global_config.env = global_data.get("env", {})
        global_config.eval_env = global_data.get("eval-env", {})
        global_config.cwd = os.getcwd()

        actions = []

        # we get basic shell configs
        for action, action_data in data.items():
            if action == "gobi":
                continue
            config = global_config.copy()
            config.shell = action_data.get("shell", config.shell)
            config.params = action_data.get("params", config.params)
            config.env = config.env | action_data.get("env", {})
            config.eval_env = config.eval_env | action_data.get("eval-env", {})
            config.cwd = action_data.get("cwd", config.cwd)
            command = action_data.get("command")
            actions.append(ShellAction("shell." + action, action, config, command))

        # we also have a special bash version for convenience
        for action, action_data in gobi_file.data.get("bash", {}).items():
            config = global_config.copy()
            config.shell = "/bin/bash"
            config.params = action_data.get("params", config.params)
            config.env = config.env | action_data.get("env", {})
            config.eval_env = config.eval_env | action_data.get("eval-env", {})
            config.cwd = action_data.get("cwd", config.cwd)
            command = action_data.get("command")
            actions.append(ShellAction("bash." + action, action, config, command))

        return actions


def create() -> Recipe:
    return ShellRecipe()
