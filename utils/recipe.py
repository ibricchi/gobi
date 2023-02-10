import os
import sys

from .state import State

class Recipe:
    def pre_action(self) -> None:
        pass

    def post_action(self) -> None:
        pass
