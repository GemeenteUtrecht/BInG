import re
from typing import Union

RE_PROJECT_ID = re.compile(r"BInG-(?P<project_id>.*)")


def match_project_id(identificatie: str) -> Union[None, str]:
    """
    Check it the identificatie matches the project ID pattern.
    """
    match = RE_PROJECT_ID.match(identificatie)
    if not match:
        return None
    return match.group("project_id")
