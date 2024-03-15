#!/usr/bin/env python3

from __future__ import annotations
import sys
import os

base_dir = os.path.dirname(os.path.realpath(__file__))

# add libs to filepath
libs_dir = os.path.join(base_dir, "libs")
sys.path.append(os.path.join(libs_dir, "tomli", "src"))
sys.path.append(os.path.join(libs_dir, "tomlkit"))

from recipes.gobi import GobiAction

if __name__ == "__main__":
    # add recipes to filepath
    sys.path.append(os.path.join(base_dir, "recipes"))
    if os.environ.get("GOBI_CUSTOM_RECIPES") is not None:
        sys.path.append(os.environ.get("GOBI_CUSTOM_RECIPES"))

    main_gobi_file = os.environ.get("GOBI_CORE_FILE", os.path.join(base_dir, "gobi.toml"))

    gobi_action = GobiAction("", main_gobi_file)
    result = gobi_action.run(None, None, None, sys.argv[1:])

    if result is not None:
        print(f"\033[31m[{result.source.name}]:")
        print(f"\033[31m{result.msg}\033[0m")
        exit(result.code)
