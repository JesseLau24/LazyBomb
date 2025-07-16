import json
import os
from typing import List, Dict
from utils.constants import TASKS_JSON_PATH  # ✅ 新增导入

# 默认路径使用 data/tasks.json
TASK_FILE = TASKS_JSON_PATH

def load_tasks(filename: str = TASK_FILE) -> List[Dict]:
    """
    Load existing tasks from a JSON file. Return empty list if file doesn't exist.
    """
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    else:
        return []

def save_tasks(tasks: List[Dict], filename: str = TASK_FILE):
    """
    Save list of task dicts to a JSON file.
    """
    with open(filename, "w") as f:
        json.dump(tasks, f, indent=2)

def append_tasks(new_tasks: List[Dict], filename: str = TASK_FILE):
    """
    Append new tasks to file. Avoid duplicates based on 'task' field.
    Ensure each task has a 'status' field (default to 'to do').
    """
    existing = load_tasks(filename)

    existing_task_names = {task["task"] for task in existing}

    # ✅ add "to do" to status (if missing)
    normalized = []
    for t in new_tasks:
        t = t.copy()
        if "status" not in t:
            t["status"] = "to do"
        normalized.append(t)

    # ✅ remove duplicates
    filtered = [t for t in normalized if t["task"] not in existing_task_names]

    if filtered:
        updated = existing + filtered
        save_tasks(updated, filename)
        print(f"✅ Added {len(filtered)} new task(s) to {filename}")
    else:
        print("📭 No new tasks to add (all duplicates)")
