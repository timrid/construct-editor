from __future__ import annotations

import typing as t


class NameExcludedFromPath(str):
    pass


class ListIndexName(str):
    pass


NameType = str | NameExcludedFromPath | ListIndexName

PathType = t.List[str | ListIndexName]


def create_path_str(path: PathType) -> str:
    path_str = ""
    for p in path:
        if isinstance(p, ListIndexName):
            path_str += f"{p}"
        else:
            path_str += f".{p}"
    if path_str.startswith("."):
        path_str = path_str[1:]
    return path_str
