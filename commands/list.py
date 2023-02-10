from utils.command import Command
from utils.state import State
from utils.action import Action
    
class ListCommand(Command):
    def __init__(self, state: State) -> None:
        self.state = state

    def run(self) -> None:
        print("Available projects:")
        projects = self.state.global_config.projects
        sorted_projects = sorted(projects)
        for project in sorted_projects:
            print(f"  {project}")

class ListAction(Action):
    def __init__(self, state: State) -> None:
        self.state = state

    def run(self) -> None:
        print("Available actions:")
        actions = self.state.actions
        sorted_actions = sorted(actions)
        for action in sorted_actions:
            print(f"  {action}")

def create(state: State) -> Command:
    state.register_action("list", ListAction(state))
    return ListCommand(state)