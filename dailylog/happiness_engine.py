# dailylog/happiness_engine.py

import os
import json
import random
from datetime import datetime, date
from pathlib import Path

from utils.constants import DATA_DIR, DAILY_LOG_FILE_TEMPLATE
from utils.file_utils import read_json, write_json
from dailylog.presets import happiness_activities


def get_log_path():
    """返回今年的 happiness 日志路径（如 2025.json）"""
    year = datetime.now().year
    log_dir = os.path.join(DATA_DIR, "daily_logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f"{year}.json")


def initialize_today_happiness_task():
    """初始化当天的每日快乐任务（如果还没有）"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    log_path = get_log_path()

    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            log_data = json.load(f)
    else:
        log_data = {}

    if today_str not in log_data:
        log_data[today_str] = {}

    if "happiness_task" not in log_data[today_str]:
        random_task = random.choice(happiness_activities)
        log_data[today_str]["happiness_task"] = {
            "task": random_task,
            "custom_text": "",       # 用户修改内容
            "image_path": "",        # 上传图片路径
            "reflection": ""         # 用户写的感想
        }
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2)

    return log_data[today_str]["happiness_task"]


def get_today_happiness_task():
    """获取今天的快乐任务（不初始化，仅读取）"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    log_path = get_log_path()

    if not os.path.exists(log_path):
        return {}

    with open(log_path, "r", encoding="utf-8") as f:
        log_data = json.load(f)

    return log_data.get(today_str, {}).get("happiness_task", {})


def update_today_happiness_reflection(reflection: str = "", image_path: str = ""):
    """更新今天的快乐任务的反思和图片路径（任意一个参数都可选）"""
    today_str = date.today().isoformat()
    year = str(date.today().year)
    filepath = DAILY_LOG_FILE_TEMPLATE.format(year=year)

    logs = read_json(filepath)
    logs.setdefault(today_str, {})

    if "happiness_task" not in logs[today_str]:
        logs[today_str]["happiness_task"] = {
            "task": "",         # 预留
            "custom_text": "",
            "image_path": "",
            "reflection": ""
        }

    # 安全更新字段
    task_entry = logs[today_str]["happiness_task"]
    if reflection:
        task_entry["reflection"] = reflection
    if image_path:
        task_entry["image_path"] = image_path

    write_json(filepath, logs)

