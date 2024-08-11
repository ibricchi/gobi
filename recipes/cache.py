from __future__ import annotations

from utils.cache import Cache
from utils.loader import GobiFile
from utils.recipes import GobiError, Action, Recipe

import os

def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


class CacheAction(Action):
    def __init__(self) -> None:
        super().__init__()
        self.name = "cache.cache"
        self.subname = "cache"

    def help(self) -> str:
        return """
Cache utility built into gobi, and used by some recipes
Cache action has two options:
Usage: gobi <project list...>? list [size|clear] [args...]

The subaction size will return the size of the current cache director
The subaction clear will clear all cached data, the option -y can be passed in to ignore the prompt
The subaction dir will return the path to the cache directory
"""

    def run(
        self,
        gobi_file: GobiFile,
        recipes: dict[str, Recipe],
        actions: list[Action],
        args: list[str],
    ) -> GobiError | None:
        non_flag_args = [a for a in args if not a.startswith("-")]
        match non_flag_args[0]:
            case "size":
                size = 0
                for f in os.listdir(Cache.cache_dir):
                    f = os.path.join(Cache.cache_dir, f)
                    if os.path.isfile(f):
                        size += os.path.getsize(f)

                print(f"Current cache size: {sizeof_fmt(size)}")
            case "clear":
                if "-y" not in args:
                    confirmation = input("Clearing cache, are you sure you want to proceed [y/N]?")
                    if confirmation != "y":
                        return GobiError(self, 1, "Aborting")
                for f in os.listdir(Cache.cache_dir):
                    ff = os.path.join(Cache.cache_dir, f)
                    if os.path.isfile(ff):
                        os.unlink(ff)
                    else:
                        return GobiError(self, 1, f"Found unexpected path in cache dir {f}")
                os.rmdir(Cache.cache_dir)
                os.mkdir(Cache.cache_dir)
            case "dir":
                print(Cache.cache_dir)
            case _:
                return GobiError(self, -1, f"Unknown arguments '{' '.join(args)}'")

class CacheRecipe(Recipe):
    def __init__(self):
        self.name = "cache"

    def create_actions(self, gobi_file: GobiFile) -> GobiError | tuple[list[Action], list[str]]:
        return [CacheAction()], []


def create() -> Recipe:
    return CacheRecipe()
