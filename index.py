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

def add_task(text: str, priority: int = 3, due: Optional[str] = None):
    tasks = load_tasks()
    t = Task(
        id=next_id(tasks),
        text=text.strip(),
        created=datetime.now().isoformat(timespec="seconds"),
        due=due,
        priority=priority,
        done=False
    )
    tasks.append(t)
    save_tasks(tasks)
    print(f"Added #{t.id}: {t.text} (p{t.priority}" + (f", due {t.due}" if t.due else "") + ")")

def list_tasks(view: str = "open"):
    tasks = load_tasks()
    if view == "open":
        tasks = [t for t in tasks if not t.done]
    elif view == "done":
        tasks = [t for t in tasks if t.done]
    # sort: status, priority, due, created
    def key(t: Task):
        due = t.due or "9999-12-31"
        return (t.done, t.priority, due, t.created)
    tasks.sort(key=key)

    if not tasks:
        print("No tasks to show.")
        return

    print(f"{'ID':>3} {'P':>1} {'Due':<10} {'Status':<7} Task")
    print("-"*60)
    today = date.today().isoformat()
    for t in tasks:
        status = "done" if t.done else ("OVERDUE" if (t.due and t.due < today) else "open")
        print(f"{t.id:>3} {t.priority:<1} {(t.due or ''):<10} {status:<7} {t.text}")

def mark_done(task_id: int):
    tasks = load_tasks()
    for t in tasks:
        if t.id == task_id:
            if t.done:
                print(f"#{t.id} already done.")
            else:
                t.done = True
                save_tasks(tasks)
                print(f"Marked #{t.id} as done.")
            return
    print(f"Task #{task_id} not found.", file=sys.stderr); sys.exit(1)

def delete_task(task_id: int):
    tasks = load_tasks()
    new = [t for t in tasks if t.id != task_id]
    if len(new) == len(tasks):
        print(f"Task #{task_id} not found.", file=sys.stderr); sys.exit(1)
    save_tasks(new)
    print(f"Deleted #{task_id}.")

def clear_tasks(clear_done: bool = False, clear_all: bool = False):
    tasks = load_tasks()
    if clear_all:
        save_tasks([]); print("Cleared ALL tasks."); return
    if clear_done:
        kept = [t for t in tasks if not t.done]
        save_tasks(kept); print("Cleared completed tasks."); return
    print("Nothing to do. Use --done or --all.")

import argparse

def valid_date(s: str) -> str:
    # simple YYYY-MM-DD validation
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return s
    except ValueError:
        raise argparse.ArgumentTypeError("Date must be YYYY-MM-DD")

def build_parser():
    p = argparse.ArgumentParser(description="Tiny To-Do (CLI)")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Add a new task")
    p_add.add_argument("text", help="Task description")
    p_add.add_argument("-p", "--priority", type=int, choices=range(1,6), default=3, help="Priority 1-5 (1=high)")
    p_add.add_argument("-d", "--due", type=valid_date, help="Due date YYYY-MM-DD")

    p_list = sub.add_parser("list", help="List tasks")
    g = p_list.add_mutually_exclusive_group()
    g.add_argument("--all", dest="view", action="store_const", const="all", help="Show all")
    g.add_argument("--open", dest="view", action="store_const", const="open", help="Only open (default)")
    g.add_argument("--done", dest="view", action="store_const", const="done", help="Only completed")
    p_list.set_defaults(view="open")

    p_done = sub.add_parser("done", help="Mark a task done by ID")
    p_done.add_argument("id", type=int)

    p_del = sub.add_parser("delete", help="Delete a task by ID")
    p_del.add_argument("id", type=int)

    p_clear = sub.add_parser("clear", help="Clear tasks")
    p_clear.add_argument("--done", action="store_true", help="Clear completed tasks")
    p_clear.add_argument("--all", action="store_true", help="Clear ALL tasks")

    return p

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "add":
        add_task(args.text, priority=args.priority, due=args.due)
    elif args.cmd == "list":
        list_tasks(view=args.view)
    elif args.cmd == "done":
        mark_done(args.id)
    elif args.cmd == "delete":
        delete_task(args.id)
    elif args.cmd == "clear":
        clear_tasks(clear_done=args.done, clear_all=args.all)

if __name__ == "__main__":
    main()
