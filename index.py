#!/usr/bin/env python3
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List
import json, sys

STORE = Path.home() / ".tiny_todo.json"

@dataclass
class Task:
    id: int
    text: str
    created: str           # ISO time
    due: Optional[str] = None  # "YYYY-MM-DD"
    priority: int = 3          # 1 (high) .. 5 (low)
    done: bool = False

def load_tasks() -> List[Task]:
    if not STORE.exists():
        return []
    try:
        data = json.loads(STORE.read_text(encoding="utf-8"))
        return [Task(**t) for t in data]
    except Exception:
        print("Data file is corrupted. Move/delete ~/.tiny_todo.json and retry.", file=sys.stderr)
        sys.exit(2)

def save_tasks(tasks: List[Task]) -> None:
    STORE.write_text(json.dumps([asdict(t) for t in tasks], indent=2), encoding="utf-8")

def next_id(tasks: List[Task]) -> int:
    return (max((t.id for t in tasks), default=0) + 1)
