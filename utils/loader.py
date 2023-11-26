from __future__ import annotations

import tomli


class GobiFile:
    path: str
    data: dict[str, any]
    error: str | None = None

    def __init__(self, path):
        self.path = path

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
