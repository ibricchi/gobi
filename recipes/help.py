from utils.containers import State, Recipe, Action
from utils.help import help_menu

class HelpAction(Action):
    state: State

    def __init__(self, state: State) -> None:
        super().__init__()
        self.state = state

    def run(self) -> None:
        help_menu()

class HelpRecipe(Recipe):
    def register_actions(self, config: dict, state: State) -> list[tuple[str, Action]]:
        return [("help", HelpAction(state))]

def create(state: State) -> Recipe:
    return HelpRecipe()
    