#!/usr/bin/env python3

from __future__ import annotations
import sys
import os
import pathlib
import shutil

base_dir = os.path.dirname(os.path.realpath(__file__))

# add libs to filepath
libs_dir = os.path.join(base_dir, "libs")
sys.path.append(os.path.join(libs_dir, "tomli", "src"))
sys.path.append(os.path.join(libs_dir, "tomlkit"))

from recipes.gobi import GobiAction
from utils.cache import Cache

if __name__ == "__main__":
    # add recipes to filepath
    sys.path.append(os.path.join(base_dir, "recipes"))
    if (custom_recipe_path := os.environ.get("GOBI_CUSTOM_RECIPES")) is not None:
        sys.path.append(custom_recipe_path)
    main_gobi_file = os.environ.get("GOBI_CORE_FILE", os.path.join(pathlib.Path.home(), ".config", "gobi", "gobi.toml"))

    # make the gobi file if not present
    if not os.path.exists(main_gobi_file):
        os.makedirs(os.path.dirname(main_gobi_file), exist_ok=True)
        shutil.copy(os.path.join(base_dir, "gobi.toml"), main_gobi_file)

    # setup cache dir if not present
    if os.path.exists(Cache.cache_dir):
        if not os.path.isdir(Cache.cache_dir):
            print(f"\033[31mExpected {Cache.cache_dir} to be a directory\033[0m")
            exit(-1)
    else:
        os.mkdir(Cache.cache_dir)

    gobi_action = GobiAction("", main_gobi_file)
    result = gobi_action.run(None, None, None, sys.argv[1:])

    if result is not None:
        print(f"\033[31m[{result.source.name}]:")
        print(f"\033[31m{result.msg}\033[0m")
        exit(result.code)
