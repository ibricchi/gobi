from __future__ import annotations
from typing import Any

from utils.recipes import Recipe, Action

import os
import pickle
import hashlib

base_dir = os.path.dirname(os.path.realpath(__file__))

class Cache:
    cache_dir = os.environ.get("GOBI_CACHE_DIR", os.path.realpath(os.path.join(base_dir, "..", ".cache")))

    @staticmethod
    def get_cache_file(action: Action | Recipe, path: str, extra: str | None = None) -> str:
        if isinstance(action, Action):
            id = f"action-{action.name}.{action.subname}"
        else:
            id = f"recipe-{action.name}"
        id = f"{id}-{path}"
        if extra is not None:
            id = f"{id}-{extra}"
        id = id.encode()
        id_hash = hashlib.md5(id, usedforsecurity=False).hexdigest()

        return os.path.join(Cache.cache_dir, id_hash)

    @staticmethod
    def try_read(action: Action | Recipe, path: str, extra: str | None = None) -> Any:
        cached_file = Cache.get_cache_file(action, path, extra)
        
        data = None
        if os.path.isfile(cached_file):
            try:
                with open(cached_file, "rb") as f:
                    data = pickle.load(f)
            except:
                pass
        
        if data is not None:
            base_time = os.path.getctime(cached_file)
            time_check = True
            for f in data.get("cache_deps", []):
                if not os.path.exists(f) or os.path.getctime(f) > base_time:
                    time_check = False
                    break
            if time_check:
                return data.get("data")
        
        if os.path.exists(cached_file):
            os.unlink(cached_file)        

    @staticmethod
    def try_store(data: Any, cache_deps: list[str], action: Action | Recipe, path: str, extra: str | None = None) -> bool:
        data = {
            "data": data,
            "cache_deps": cache_deps
        }
        cached_file = Cache.get_cache_file(action, path, extra)
        if os.path.exists(cached_file):
            os.unlink(cached_file)
        try:
            with open(cached_file, "w+b") as f:
                pickle.dump(data, f)
                return True
        except:
            if os.path.exists(cached_file):
                os.unlink(cached_file)
        finally:
            return False
