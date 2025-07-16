import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# 数据文件夹
DATA_DIR = os.path.join(BASE_DIR, "data")

# 各类 JSON 文件路径
TASKS_JSON_PATH = os.path.join(DATA_DIR, "tasks.json")
LAST_PROCESSED_JSON_PATH = os.path.join(DATA_DIR, "last_processed.json")
STRIKE_LOG_PATH = os.path.join(DATA_DIR, "strike_log.json")

# ✅ 统一提醒 + 惩罚视频文件夹路径
ALERT_VIDEO_DIR = os.path.join(BASE_DIR, "assets", "alerts")

# ✅ 支持的视频扩展名
ALERT_VIDEO_EXT = ".mp4"
