from app.models import TelexMessageEvent
import re
from typing import Optional

# Very simple heuristics: typical task keywords or bullet patterns
TASK_KEYWORDS = [
    r"\btask\b", r"\bdeadline\b", r"\bdeliverable\b", r"\baction\b",
    r"\bplease\s+(?:do|complete|implement|review)\b", r"\bby\s+[A-Z][a-z]+ \d{1,2}\b"
]

def looks_like_task(content: str) -> bool:
    s = content.lower()
    for k in TASK_KEYWORDS:
        if re.search(k, s, re.I):
            return True
    # bullets or checklist
    if re.search(r"^- \[ \] |^- \[x\]", content, re.M):
        return True
    # phrases like "We need X by DATE"
    if re.search(r"\bby\s+\w+\s+\d{1,2}(?:,?\s+\d{4})?\b", content, re.I):
        return True
    return False

def extract_title(content: str) -> str:
    # best-effort: first line up to 80 chars
    first_line = content.strip().splitlines()[0]
    return first_line[:150]

def extract_deadline(content: str) -> Optional[str]:
    m = re.search(r"by\s+([A-Z][a-z]+\s+\d{1,2}(?:,?\s+\d{4})?)", content)
    if m:
        return m.group(1)
    m2 = re.search(r"deadline[:\s]*([0-9T:\-\/ ]+)", content, re.I)
    if m2:
        return m2.group(1)
    return None
