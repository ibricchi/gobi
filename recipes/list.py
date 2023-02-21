from utils.containers import State, Recipe, Action

class ListAction(Action):
    def run(self, state: State) -> None:
        print("Available actions:")
        for action_name in sorted(state.project.actions.keys()):
            print(f"  {action_name}")

class ListRecipe(Recipe):
    def register_actions(self, config: dict, state: State) -> list[tuple[str, Action]]:
        return [("list", ListAction())]

def create(state: State) -> Recipe:
    return ListRecipe()
    
