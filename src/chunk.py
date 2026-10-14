"""Split the course documents into chunks that each answer one kind of question.

One chunk per `## ` section, because the course pages are written that way (one topic per
heading). A section longer than MAX_CHARS is split on paragraphs, and each piece repeats the
last paragraph of the piece before it (the overlap), so a deadline that sits on a boundary is
never cut in half.

Every chunk carries its document title and section heading, prepended to the embedded text,
so "Homework" in Lab 1 and "Homework" in Lab 4 do not look identical to the retriever.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

MAX_CHARS = 1200      # about 300 tokens of English
OVERLAP_PARAS = 1


@dataclass
class Chunk:
    id: str           # "milestones/hw1#4"
    doc_id: str       # "milestones/hw1": the path under data/corpus without .md
    title: str        # the document's first "# " heading
    section: str      # the "## " heading
    text: str

    def embed_text(self) -> str:
        return f"{self.title} · {self.section}\n{self.text}"

    def to_dict(self) -> dict:
        return asdict(self)


def _split_long(text: str) -> list[str]:
    if len(text) <= MAX_CHARS:
        return [text]
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    pieces, current = [], []
    for p in paras:
        if current and len("\n\n".join(current + [p])) > MAX_CHARS:
            pieces.append("\n\n".join(current))
            current = current[-OVERLAP_PARAS:] if OVERLAP_PARAS else []
        current.append(p)
    if current:
        pieces.append("\n\n".join(current))
    return pieces


def chunk_markdown(doc_id: str, markdown: str) -> list[Chunk]:
    lines = markdown.strip().splitlines()
    title = lines[0].lstrip("# ").strip() if lines and lines[0].startswith("# ") else doc_id
    sections: list[tuple[str, list[str]]] = []
    for line in lines[1:]:
        if line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif sections:
            sections[-1][1].append(line)
        elif line.strip():
            sections.append(("Overview", [line]))
    chunks: list[Chunk] = []
    for section, body in sections:
        text = "\n".join(body).strip()
        if not text:
            continue
        for piece in _split_long(text):
            chunks.append(Chunk(f"{doc_id}#{len(chunks) + 1}", doc_id, title, section, piece))
    return chunks


def load_corpus(root: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(root.rglob("*.md")):
        doc_id = path.relative_to(root).with_suffix("").as_posix()
        chunks.extend(chunk_markdown(doc_id, path.read_text(encoding="utf-8")))
    return chunks
