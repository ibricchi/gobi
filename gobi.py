#!/usr/bin/env python3

from __future__ import annotations
import argparse

from utils.config import Environment, GlobalConfig
from utils.recipie import load_recipie
from utils.state import State
from utils.tools import load_tools

if __name__ == "__main__":
    state = State()

    parser = argparse.ArgumentParser()
    parser.add_argument("project", help="Project to perform action on")
    parser.add_argument("action", help="Action to perform")

    args, unknown = parser.parse_known_args()

    state.set("args", unknown) 

    env = Environment.default()
    state.set("env", env)

    global_config = GlobalConfig(env)
    state.set("global_config", global_config)
    
    project_config = global_config.get_project(args.project)
    state.set("project_config", project_config)

    tools = load_tools(state)
    state.set("tools", tools)

    action_config = project_config.get_action(args.action)
    state.set("action_config", action_config)

    for tool in tools:
        tool.run_before_recipie_load()

    recipie = load_recipie(state)

    for tool in tools:
        tool.run_after_before_recipie_run()

    recipie.run()

    for tool in tools:
        tool.run_after_recipie_run()