from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_LINE_COMMENT = re.compile(r"(^|\s)//.*?$", re.MULTILINE)
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


def loads_jsonc(text: str) -> Any:
    """
    Parse JSON-with-comments (// and /* */).
    Your `data/job_source.json` contains `//` comments, so normal json.loads fails.
    """
    no_block = re.sub(_BLOCK_COMMENT, "", text)
    no_line = re.sub(_LINE_COMMENT, r"\1", no_block)
    return json.loads(no_line)


def load_jsonc(path: str | Path, *, encoding: str = "utf-8") -> Any:
    p = Path(path)
    return loads_jsonc(p.read_text(encoding=encoding))

