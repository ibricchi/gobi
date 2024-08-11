from __future__ import annotations

import os
from tomlkit import dumps, parse

from utils.loader import GobiFile
from utils.recipes import GobiError, Action, Recipe


class ProjectManagerWhereAction(Action):
    def __init__(self) -> None:
        super().__init__()
        self.name = "project-manager.where"
        self.subname = "where"

    def help(self) -> str:
        return """
Get the path of a projects gobi file

Usage: gobi <project list...>? where <project name>
"""

    def run(
        self,
        gobi_file: GobiFile,
        recipes: dict[str, Recipe],
        actions: list[Action],
        args: list[str],
    ) -> GobiError | None:
        if len(args) == 0:
            return GobiError(self, 1, "No project name specified")
        project_data = gobi_file.data.get("gobi", {}).get("projects", {})
        if args[0] not in project_data:
            return GobiError(self, 1, f"Project {args[0]} not found")
        print(project_data[args[0]])


class ProjectManagerRegisterAction(Action):
    def __init__(self) -> None:
        super().__init__()
        self.name = "project-manager.register"
        self.subname = "register"

    def help(self) -> str:
        return """
Register a project to a gobi file

Usage: gobi <project list...>? register <project name> <gobi file path>

project name: name of the action that will load the project

gobi file path: path to the gobi file for the project
"""

    def run(
        self,
        gobi_file: GobiFile,
        recipes: dict[str, Recipe],
        actions: list[Action],
        args: list[str],
    ) -> GobiError | None:
        match len(args):
            case 0:
                return GobiError(self, 1, "No project name or gobi file path specified")
            case 1:
                return GobiError(self, 1, "No gobi file path specified")
            case _:
                pass

        project_name = args[0]
        gobi_file_path = args[1]

        # reload gobi file using tomlkit
        gobi_file_data = parse(open(gobi_file.path).read())

        # check if gobi file has gobi.projects
        if "gobi" not in gobi_file_data:
            gobi_file_data["gobi"] = {}
        if "projects" not in gobi_file_data["gobi"]:
            gobi_file_data["gobi"]["projects"] = {}

        # check if project already exists
        if project_name in gobi_file_data["gobi"]["projects"]:
            return GobiError(self, 1, f"Project {project_name} already exists")

        # check that path exists
        if not os.path.exists(gobi_file_path):
            return GobiError(self, 1, f"Gobi file {gobi_file_path} does not exist")

        # expand path to absolute path
        gobi_file_path = os.path.abspath(gobi_file_path)

        # add project to gobi file
        gobi_file_data["gobi"]["projects"][project_name] = gobi_file_path

        # write gobi file
        with open(gobi_file.path, "w") as f:
            f.write(dumps(gobi_file_data))

        # reload gobi file data
        new_gobi_file = GobiFile(gobi_file.path)
        gobi_file.data = new_gobi_file.data


class ProjectManagerDeregisterAction(Action):
    def __init__(self) -> None:
        super().__init__()
        self.name = "project-manager.deregister"
        self.subname = "deregister"

    def help(self) -> str:
        return """
Deregister a project from a gobi file

Usage: gobi <project list...>? deregister <project name>

project name: name of the action that will load the project
"""

    def run(
        self,
        gobi_file: GobiFile,
        recipes: dict[str, Recipe],
        actions: list[Action],
        args: list[str],
    ) -> GobiError | None:
        if len(args) == 0:
            return GobiError(self, 1, "No project name specified")

        project_name = args[0]

        # check if gobi file has gobi.projects
        if (
            "gobi" not in gobi_file.data
            or "projects" not in gobi_file.data["gobi"]
            or project_name not in gobi_file.data["gobi"]["projects"]
        ):
            return GobiError(self, 1, f"Project {project_name} does not exist")

        # reload gobi file using tomlkit
        gobi_file_data = parse(open(gobi_file.path).read())
        gobi_file_data["gobi"]["projects"].pop(project_name)

        # write gobi file
        with open(gobi_file.path, "w") as f:
            f.write(dumps(gobi_file_data))

        # reload gobi file data
        new_gobi_file = GobiFile(gobi_file.path)
        gobi_file.data = new_gobi_file.data


class ProjectManagerPruneAction(Action):
    def __init__(self) -> None:
        super().__init__()
        self.name = "project-manager.prune"
        self.subname = "prune"

    def help(self) -> str:
        return """
Prune projects from the current gobi file that no longer exist

Usage: gobi <project list...>? prune [-y]

-y: skip confirmation prompt
"""

    def run(
        self,
        gobi_file: GobiFile,
        recipes: dict[str, Recipe],
        actions: list[Action],
        args: list[str],
    ) -> GobiError | None:
        # check if gobi file has gobi.projects
        if "gobi" not in gobi_file.data or "projects" not in gobi_file.data["gobi"]:
            print("All clean!")
            return

        # loop through projects and gather non existent paths
        projects_to_remove = []
        for project_name, project_path in gobi_file.data["gobi"]["projects"].items():
            if not os.path.exists(project_path):
                projects_to_remove.append(project_name)

        if len(projects_to_remove) == 0:
            print("All clean!")
            return

        can_pop = False
        if len(args) > 0 and args[0] == "-y":
            can_pop = True
        else:
            print("The following projects will be removed:")
            for project in projects_to_remove:
                print(f"  {project}")
            print("Are you sure you want to continue? (y/n)")
            answer = input()
            if answer == "y":
                can_pop = True

        if not can_pop:
            return GobiError(self, 1, "Aborting prune")

        # reload gobi file using tomlkit
        gobi_file_data = parse(open(gobi_file.path).read())

        # pop projects
        for project in projects_to_remove:
            gobi_file_data["gobi"]["projects"].pop(project)

        # write gobi file
        with open(gobi_file.path, "w") as f:
            f.write(dumps(gobi_file_data))

        # reload gobi file data
        new_gobi_file = GobiFile(gobi_file.path)
        gobi_file.data = new_gobi_file.data

        print("All clean!")


class ProjectManagerRecipe(Recipe):
    def __init__(self):
        self.name = "project-manager"

    def create_actions(self, gobi_file: GobiFile) -> GobiError | tuple[list[Action], list[str]]:
        return [
            ProjectManagerWhereAction(),
            ProjectManagerRegisterAction(),
            ProjectManagerDeregisterAction(),
            ProjectManagerPruneAction(),
        ], []


def create() -> Recipe:
    return ProjectManagerRecipe()
