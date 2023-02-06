#!/usr/bin/env python3

from __future__ import annotations
import sys
import argparse
import tomli
import os
from dataclasses import dataclass

from utils.config import Environment, GlobalConfig
from utils.recipie import load_recipie

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="Action to perform")
    parser.add_argument("project", help="Project to perform action on")

    args, unknown = parser.parse_known_args()

    env = Environment.default()

    global_config = GlobalConfig(env)
    project_config = global_config.get_project(args.project)
    action_config = project_config.get_action(args.action)

    recipie = load_recipie(env, global_config, project_config, action_config, unknown)

    recipie.run()
