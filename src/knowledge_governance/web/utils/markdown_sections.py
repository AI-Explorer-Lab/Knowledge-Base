from __future__ import annotations

import re
from typing import Dict, Iterable


SECTION_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def parse_sections(body: str) -> Dict[str, str]:
    matches = list(SECTION_PATTERN.finditer(body))
    result: Dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        result[match.group(1).strip()] = body[start:end].strip()
    return result


def render_body(title: str, sections: Dict[str, str], ordered_names: Iterable[str]) -> str:
    lines = [f"# {title}", ""]
    for name in ordered_names:
        lines.extend([f"## {name}", "", sections[name].strip(), ""])
    return "\n".join(lines).rstrip() + "\n"
