from __future__ import annotations
from typing import Any

import tomli

class GobiFile:
    path: str
    data: dict[str, Any]
    error: str | None = None
    cacheable: bool

    def __init__(self, path):
        self.path = path
        self.cacheable = True

        try: 
            with open(path, "rb") as f:
                self.data = tomli.load(f)
        except tomli.TOMLDecodeError as e:
            self.error = "Could not parse TOML file"
            self.data = {}
        except FileNotFoundError as e:
            self.error = "File does not exist"
            self.data = {}
        except PermissionError as e:
            self.error = "Permission denied"
            self.data = {}
        except Exception as e:
            self.error = "Unknown error"
            self.data = {}
