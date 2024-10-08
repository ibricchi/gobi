from __future__ import annotations

from utils.loader import GobiFile
from utils.recipes import GobiError, Action, Recipe


class TemplateAction(Action):
    def __init__(self) -> None:
        super().__init__()
        self.name = "template"
        self.subname = "template"

    def run(
        self,
        gobi_file: GobiFile,
        recipes: dict[str, Recipe],
        actions: list[Action],
        args: list[str],
    ) -> GobiError | None:
        pass

class TemplateRecipe(Recipe):
    def __init__(self):
        self.name = "template"

    def create_actions(self, gobi_file: GobiFile) -> GobiError | tuple[list[Action], list[str]]:
        return [TemplateAction()], []


def create() -> Recipe:
    return TemplateRecipe()
