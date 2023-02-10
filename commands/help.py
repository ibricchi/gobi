from utils.command import Command
from utils.state import State
from utils.help import help_menu
from utils.action import Action

class HelpCommand(Command):
    def run(self) -> None:
        help_menu()

def create(state: State) -> Command:
    return HelpCommand()