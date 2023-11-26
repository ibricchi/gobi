from __future__ import annotations

from utils.loader import GobiFile 
from utils.recipes import GobiError, Action, Recipe, load_recipe


class GobiAction(Action):
    def __init__(self, subname: str, path: str) -> None:
        if subname == "":
            self.name = "gobi"
        else:
            self.name = f"gobi.{subname}"
        self.subname = subname
        self.path = path

    def run(
        self,
        _gobi_file: GobiFile,
        _recipes: dict[str, Recipe],
        _actions: dict[str, Action],
        args: list[str],
    ) -> GobiError | None:
        gobi_file: GobiFile = GobiFile(self.path)

        if gobi_file.error:
            return GobiError(self, 1, f"Could not load gobi file: {gobi_file.error}")

        gobi_recipe = GobiRecipe()
        gobi_actions = gobi_recipe.create_actions(gobi_file)
        if isinstance(gobi_actions, GobiError):
            return gobi_actions

        if len(args) == 0:
            return GobiError(self, 1, "No action specified")

        # find actions with matching subname
        possible_actions = list(filter(lambda a: a.subname == args[0], gobi_actions))
        match possible_actions:
            case []:
                # try finding actions with matching name
                possible_actions = list(filter(lambda a: a.name == args[0], gobi_actions))
                if len(possible_actions) == 0:
                    return GobiError(self, 1, f"Unknown action: {args[0]}")
                if len(possible_actions) == 1:
                    return possible_actions[0].run(
                        gobi_file, gobi_recipe.current_recipes, gobi_actions, args[1:]
                    )
                return GobiError(self, 1, f"INTERNAL ERROR: Multiple actions with name {args[0]}")
            case [action]:
                return action.run(
                    gobi_file, gobi_recipe.current_recipes, gobi_actions, args[1:]
                )
            case _:
                return GobiError(self, 1, "Too many actions with subname {}, use full name from:\n  {}".format(
                    args[0], "\n  ".join(map(lambda a: a.name, possible_actions))
                ))


class GobiRecipe(Recipe):
    loaded_recipes: dict[str, Recipe] = {}
    permanent_recipes: dict[str, Recipe] = {}
    current_recipes: dict[str, Recipe]

    def __init__(self) -> None:
        self.name = "gobi"

    def create_actions(self, gobi_file: GobiFile) -> GobiError | list[Action]:
        config = gobi_file.data.get("gobi", {})

        # get actions from permanent recipes
        actions: list[Action] = []
        for _, recipe in GobiRecipe.permanent_recipes.items():
            recipe_actions = recipe.create_actions(gobi_file)
            if isinstance(recipe_actions, GobiError):
                return recipe_actions
            actions += recipe_actions

        # load recipes
        recipe_names = config.get("recipes", [])
        recipes: dict[str, Recipe] = {}
        for recipe_name in recipe_names:
            if recipe_name in GobiRecipe.permanent_recipes:
                continue

            if recipe_name not in GobiRecipe.loaded_recipes:
                new_recipe = load_recipe(recipe_name)
                if new_recipe is None:
                    return GobiError(self, 1, f"Could not find {recipe_name}.py, if using a custom recipe, make sure to add it to GOBI_RECIPE_PATH")
                GobiRecipe.loaded_recipes[recipe_name] = new_recipe

            recipes[recipe_name] = GobiRecipe.loaded_recipes[recipe_name]

        # get their actions
        for _, recipe in recipes.items():
            recipe_actions = recipe.create_actions(gobi_file)
            if isinstance(recipe_actions, GobiError):
                return recipe_actions
            actions += recipe_actions

        # add both to list of current recipes
        self.current_recipes = GobiRecipe.permanent_recipes | recipes

        # load child_recipes
        child_recipe_names = config.get("child-recipes", [])
        for recipe_name in child_recipe_names:
            if recipe_name in GobiRecipe.permanent_recipes:
                continue
            if recipe_name not in GobiRecipe.loaded_recipes:
                GobiRecipe.loaded_recipes[recipe_name] = load_recipe(recipe_name)
                continue
            GobiRecipe.permanent_recipes[recipe_name] = GobiRecipe.loaded_recipes[
                recipe_name
            ]

        # load gobi actions
        gobi_projects = config.get("projects", {})
        for project_name, project_path in gobi_projects.items():
            actions.append(GobiAction(project_name, project_path))

        return actions


def create() -> Recipe:
    return GobiRecipe()
