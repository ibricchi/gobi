from __future__ import annotations

from .help import help_menu

class Action:
    def run(self) -> None:
        raise NotImplementedError()

class ListAction(Action):
    def run(self) -> None:
        print("Available actions:")
        for project in self.state.global_config.projects:
            print(f"  {project}")

class HelpAction(Action):
    def run(self) -> None:
        help_menu()

def get_default_commands() -> dict[str: Action]:
    return {
        "list": ListAction(),
        "help": HelpAction()
    }