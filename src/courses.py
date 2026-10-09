"""Load a course document and split it into sections at '## ' headings."""
import re
from dataclasses import dataclass
from pathlib import Path

COURSES_DIR = Path(__file__).resolve().parent.parent / "data" / "courses"
_SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


@dataclass(frozen=True)
class Section:
    title: str
    text: str


def load_course(course_id: str) -> list[Section] | None:
    """Return the course's sections, or None if the id is unknown or unsafe."""
    if not _SAFE_ID.match(course_id):
        return None
    path = COURSES_DIR / f"{course_id}.md"
    if not path.is_file():
        return None

    sections: list[Section] = []
    title, lines = None, []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if title and "".join(lines).strip():
                sections.append(Section(title, "\n".join(lines).strip()))
            title, lines = line[3:].strip(), []
        elif title is not None:
            lines.append(line)
    if title and "".join(lines).strip():
        sections.append(Section(title, "\n".join(lines).strip()))
    return sections
