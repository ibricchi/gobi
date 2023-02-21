#!/usr/bin/env python3

from __future__ import annotations
import sys

from utils.containers import State, Environment
from utils.project import run_project

if __name__ == "__main__":
    state = State()

    state.set_env(Environment.default())
    state.set_args(sys.argv)

    sys.path.append(state.env.recipe_folder)

    # load base project
    run_project("gobi", state.env.config_project_path, state)