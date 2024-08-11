from __future__ import annotations
import tempfile

import urllib
import urllib.request

from utils.loader import GobiFile
from utils.recipes import GobiError, Action, Recipe, load_recipe
from utils.cache import Cache

import os

class GobiAction(Action):
    def __init__(self, subname: str, path: str, alt_path: str | None = None) -> None:
        super().__init__()
        if subname == "":
            self.name = "gobi"
        else:
            self.name = f"gobi.{subname}"
        self.subname = subname
        self.path = path
        self.alt_path = alt_path

    def help(self) -> str:
        gobi_file: GobiFile = GobiFile(self.path)
        if gobi_file.error:
            return "Tried to load help menu from {1}{2}, but got error: {3}".format(
                self.path,
                "" if self.alt_path is None else f" ({self.alt_path})",
                gobi_file.error
            )
        return gobi_file.data.get("gobi", {}).get(
            "help", f"Project {self.subname} has no help menu"
        )

    def run(
        self,
        _gobi_file: GobiFile | None,
        _recipes: dict[str, Recipe] | None,
        _actions: dict[str, Action] | None,
        args: list[str],
    ) -> GobiError | None:
        # try to load from cache
        cached_data = Cache.try_read(self, self.path)
        if cached_data is None:
            gobi_file: GobiFile = GobiFile(self.path)
            data_to_cache = {
                "gobi-file": gobi_file
            }
            Cache.try_store(data_to_cache   , [self.path], self, self.path)
        else:
            gobi_file: GobiFile = cached_data["gobi-file"]

        if gobi_file.error:
            return GobiError(self, 1, f"Could not load gobi file: {gobi_file.error}")

        gobi_recipe = GobiRecipe()
        gobi_action_info = gobi_recipe.create_actions(gobi_file)
        if isinstance(gobi_action_info, GobiError):
            return gobi_action_info
        gobi_recipe.current_recipes["gobi"] = gobi_recipe
        gobi_actions, gobi_deps = gobi_action_info

        if len(args) == 0:
            return GobiError(self, 1, "No action specified")

        # find actions with matching subname
        possible_actions = [a for a in gobi_actions if a.subname == args[0]]
        
        # if we have multiple only consider those with priority
        if len(possible_actions) > 1:
            possible_actions = [a for a in possible_actions if a.priority]
        
        # if we don't have any then try and math full name
        if len(possible_actions) == 0:
            possible_actions = [a for a in gobi_actions if a.name == args[0] ]

        if len(possible_actions) != 1:
            return GobiError(self, 1, f"Unknon action: {args[0]}")

        action = possible_actions[0]
        os.environ["GOBI_PROJECT"] = self.subname
        os.environ["GOBI_ACTION"] = action.subname
        os.environ["GOBI_PATH"] = self.path
        if self.alt_path is not None:
            os.environ["GOBI_ALT_PATH"] = self.alt_path
        return action.run(
            gobi_file, gobi_recipe.current_recipes, gobi_actions    , args[1:]
        )

class GobiRemoteCacheAction(Action):
    def __init__(self, paths: list[tuple[str, str]]) -> None:
        super().__init__()
        self.name = "gobi.remote-cache"
        self.subname = "remote-cache"
        self.paths = paths

    def help(self) -> str:
        return """
Manage caches of remote-project configs in this file
Usage: gobi <project list...>? remote-cache [clear|show] [args...]

The subaction clear will clear all cached data, the option -y can be passed in to ignore the prompt
The subaction show will show the path to where the cached version of the remote gobi file is stored
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
            case "clear":
                if "-y" not in args:
                    confirmation = input("Clearing cache, are you sure you want to proceed [y/N]?")
                    if confirmation != "y":
                        return GobiError(self, 1, "Aborting")
                for _, f in self.paths:
                    if os.path.isfile(f):
                        os.unlink(f)
                    else:
                        return GobiError(self, 1, f"Found unexpected path in cache dir {f}")
                os.rmdir(Cache.cache_dir)
                os.mkdir(Cache.cache_dir)
            case "info":
                for name, f in sorted(self.paths, key=lambda p: p[1]):
                    print(f"{name}: {f}")
            case _:
                return GobiError(self, -1, f"Unknown arguments '{' '.join(args)}'")

class GobiRecipe(Recipe):
    loaded_recipes: dict[str, Recipe] = {}
    permanent_recipes: dict[str, Recipe] = {}
    current_recipes: dict[str, Recipe]

    def __init__(self) -> None:
        self.name = "gobi"
    
    def help(self) -> str:
        return """
This recipe is automatically loaded by gobi, and is used to load and process gobi files. It is responsible for loading and calling all other recipes, and for triggering actions.

This recipe uses the following configuration options:

[gobi.recipes] : list[str]
    list of child recipes to load

[gobi.child-recipes] : list[str]
    list of child recipes to load, that are not loaded by default

[gobi.help] : str
    help menu entry for the action created for a file

[gobi.projects] : dict[str, str]:
    dictionary of project names to paths, used to create actions for gobi files
"""

    def create_actions(self, gobi_file: GobiFile) -> GobiError | tuple[list[Action], list[str]]:
        config = gobi_file.data.get("gobi", {})

        # try to load cached data
        cached_data = Cache.try_read(self, gobi_file.path)

        # load recipes
        recipe_names = config.get("recipes", [])
        recipes: dict[str, Recipe] = {}
        for recipe_name in recipe_names:
            if recipe_name in GobiRecipe.permanent_recipes:
                continue

            if recipe_name not in GobiRecipe.loaded_recipes:
                new_recipe = load_recipe(recipe_name)
                if new_recipe is None:
                    return GobiError(
                        self,
                        1,
                        f"Could not find {recipe_name}.py, if using a custom recipe, make sure to add it to GOBI_RECIPE_PATH",
                    )
                GobiRecipe.loaded_recipes[recipe_name] = new_recipe

            recipes[recipe_name] = GobiRecipe.loaded_recipes[recipe_name]

        self.current_recipes = GobiRecipe.permanent_recipes | recipes

        # load child_recipes
        child_recipe_names = config.get("child-recipes", [])
        for recipe_name in child_recipe_names:
            if recipe_name in GobiRecipe.permanent_recipes:
                continue
            if recipe_name not in GobiRecipe.loaded_recipes:
                recipe = load_recipe(recipe_name)
                if recipe is None:
                    return GobiError(self, -1, f"Couldn't load recipe {recipe_name}")
                GobiRecipe.loaded_recipes[recipe_name] = recipe
                continue
            GobiRecipe.permanent_recipes[recipe_name] = GobiRecipe.loaded_recipes[
                recipe_name
            ]

        # early exit if we had a cache hit
        if cached_data is not None:
            return cached_data["actions"], []

        # create cactions
        actions: list[Action] = []
        deps: list[str] = []
        for _, recipe in self.current_recipes.items():
            recipe_actions_info = recipe.create_actions(gobi_file)
            if isinstance(recipe_actions_info, GobiError):
                return recipe_actions_info
            recipe_actions, recipe_deps = recipe_actions_info
            actions.extend(recipe_actions)
            deps.extend(recipe_deps)

        # load gobi actions
        gobi_projects = config.get("projects", {})
        for project_name, project_path in gobi_projects.items():
            actions.append(GobiAction(project_name, project_path))

        # load gobi remote projects
        gobi_remote_projects = config.get("remote-projects", {})
        cached_url_files = []
        for project_name, project_url in gobi_remote_projects.items():
            url_file = Cache.get_cache_file(self, project_url, "file")
            cached_url_files.append(tuple([project_name, url_file]))

            if (cached_data := Cache.try_read(self, project_url)) is not None:
                actions.append(cached_data["remote-gobi-action"])
                continue
            
            if not os.path.exists(url_file) or not Cache.enabled:
                urllib.request.urlretrieve(project_url, url_file)

            action = GobiAction(project_name, url_file, project_url)
            data_to_cache = {
                "remote-gobi-action": action
            }
            Cache.try_store(data_to_cache, [url_file], self, project_url)
            actions.append(action)

        actions.append(GobiRemoteCacheAction(cached_url_files))

        # this is to avoid gobi_files from tmp files    
        if gobi_file.cacheable:
            data_to_cache = {
                "actions": actions
            }
            Cache.try_store(data_to_cache, [gobi_file.path, *deps], self, gobi_file.path)

        return actions, []


def create() -> Recipe:
    return GobiRecipe()
