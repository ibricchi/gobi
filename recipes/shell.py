from __future__ import annotations

import os
import shutil
import subprocess as sp
import tempfile as tf
from string import Template
import time

from utils.loader import GobiFile
from utils.recipes import GobiError, Action, Recipe


class ShellConfig:
    shell: str
    extension: str
    params: list[str]
    env: dict[str, str]
    eval_env: dict[str, str]
    cwd: str
    help: str

    def copy(self) -> ShellConfig:
        new = ShellConfig()
        new.shell = self.shell
        new.extension = self.extension
        new.params = self.params.copy()
        new.env = self.env.copy()
        new.eval_env = self.eval_env.copy()
        new.cwd = self.cwd
        new.help = self.help
        return new


class ShellAction(Action):
    config: ShellConfig
    command: str

    def help(self) -> str:
        return self.config.help

    def __init__(self, name, subname, config, command) -> None:
        super().__init__()
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
        eval_env_cwd = os.path.dirname(gobi_file.path)
        for key, value in self.config.eval_env.items():
            command_file = tf.NamedTemporaryFile(
                mode="w",
                suffix=self.config.extension,
                delete=False,
            )
            command_file.write(value)
            command_file.close()
            res = sp.run(
                command_base + [command_file.name],
                cwd = eval_env_cwd,
                capture_output=True,
                text=True,
                env=env,
            )
            os.remove(command_file.name)
            if res.returncode != 0:
                return GobiError(
                    self,
                    res.returncode,
                    "Shell action failed to setup eval envs, failed at " + key,
                )
            env[key] = res.stdout.strip()

        # add normal env
        for key, value in self.config.env.items():
            env[key] = Template(value).safe_substitute(env)

        # make sure cwd dir exist
        cwd = Template(self.config.cwd).safe_substitute(env)
        if not os.path.isdir(cwd):
            return GobiError(self, 1, f"cwd '{cwd}' does not exist")

        # run command
        command_file = tf.NamedTemporaryFile(
            mode="w",
            suffix=self.config.extension,
            delete=False,
        )
        command_file.write(self.command)
        command_file.close()
        res = sp.run(
            command_base + [command_file.name] + args,
            env=env,
            cwd=cwd,
        )
        os.remove(command_file.name)

        if res.returncode != 0:
            return GobiError(self, res.returncode, "Shell command failed")


class ShellRecipe(Recipe):
    def __init__(self):
        self.name = "shell"

    def help(self) -> str:
        return """
Generate shell actions:

Shell actions run a shell command by creating a temporary with the "command" parameter, and running '[shell] [params] [command file] [args]'. Where shell, params, and command are specified per action, and args, are any arguments passed through the command line.

This recipe uses the following configuration options:

[shell.<action name>.command] (required) : str
    command to run

[shell.<action name>.shell] (optional) : str
    shell to use, defaults to /bin/sh

[shell.<action name>.extension] (optional) : str
    extension to set for the command file, defaults to empty string (mostly useful for windows)

[shell.<action name>.params] (optional) : list[str]
    list of params to pass to shell, defaults to []

[shell.<action name>.env] (optional) : dict[str, str]
    dict of env variables to set, defaults to {}, values are processed as if they are string.Template objects

[shell.<action name>.eval-env] (optional) : dict[str, str]
    dict of env variables to set, defaults to {}, values are run as shell commands from the directory of the gobi file. These are set before the normal env variables.

[shell.<action name>.cwd] (optional) : str
    directory to run the command in, defaults to the current working directory

[shell.<action name>.help] (optional) : str
    help menu entry for the action created for a file

The action name "gobi" is reserved to override default shell config for all actions in the project. "command" cannot provide defaults.
"""

    def create_actions(self, gobi_file: GobiFile) -> GobiError | tuple[list[Action], list[str]]:
        data = gobi_file.data.get("shell", {})

        # first we get the global shell config
        global_data = data.get("gobi", {})
        global_config = ShellConfig()
        global_config.shell = global_data.get("shell", "/bin/sh")
        global_config.extension = global_data.get("extension", "")
        global_config.params = global_data.get("params", [])
        global_config.env = global_data.get("env", {})
        global_config.eval_env = global_data.get("eval-env", {})
        global_config.cwd = global_data.get("cwd", os.getcwd())
        global_config.help = global_data.get("help", "No help provided")

        actions = []

        # we get basic shell configs
        for action, action_data in data.items():
            if action == "gobi":
                continue
            config = global_config.copy()
            config.shell = action_data.get("shell", config.shell)
            config.extension = action_data.get("extension", config.extension)
            config.params = action_data.get("params", config.params)
            config.env = config.env | action_data.get("env", {})
            config.eval_env = config.eval_env | action_data.get("eval-env", {})
            config.cwd = action_data.get("cwd", config.cwd)
            config.help = action_data.get("help", config.help)
            command = action_data.get("command")
            actions.append(ShellAction("shell." + action, action, config, command))

        return actions, []


def create() -> Recipe:
    return ShellRecipe()
