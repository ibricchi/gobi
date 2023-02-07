#!/usr/bin/env python3

from __future__ import annotations
import argparse

from utils.config import Environment, GlobalConfig
from utils.recipie import load_recipie
from utils.state import State

if __name__ == "__main__":
    state = State()

    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="Action to perform")
    parser.add_argument("project", help="Project to perform action on")

    args, unknown = parser.parse_known_args()

    state.set("args", args)
    state.set("unknown", unknown) 

    env = Environment.default()
    state.set("env", env)

    global_config = GlobalConfig(env)
    project_config = global_config.get_project(args.project)
    action_config = project_config.get_action(args.action)
    state.set("global_config", global_config)
    state.set("project_config", project_config)
    state.set("action_config", action_config)

    recipie = load_recipie(state)

    recipie.run()
