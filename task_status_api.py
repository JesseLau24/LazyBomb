from flask import Flask, request, jsonify, render_template, make_response, send_file
from flask_cors import CORS
from task_storage.task_status_updater import update_task_status
from task_storage.task_writer import append_tasks  
from utils.html_generator import generate_task_html_from_json
from utils.constants import TASKS_JSON_PATH
from dailylog.health_tracker import get_today_health_goals, update_health_goal_status, update_health_status
import json
import os

app = Flask(__name__)
CORS(app)

def load_tasks():
    if not os.path.exists(TASKS_JSON_PATH):
        return []
    with open(TASKS_JSON_PATH, encoding='utf-8') as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

@app.route('/', methods=['GET'])
def show_task_list():
    tasks = load_tasks()
    rendered_html = render_template('tasklist.html.j2', tasks=tasks)
    response = make_response(rendered_html)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.get_json()
    task_id = data.get('id')
    new_status = data.get('status')

    if not task_id or not new_status:
        return jsonify({"error": "Missing 'id' or 'status' in request"}), 400

    tasks = load_tasks()
    updated = False
    for t in tasks:
        if t.get("id") == task_id:
            t["status"] = new_status
            updated = True
            break

    if updated:
        save_tasks(tasks)
        return jsonify({"message": "Status updated"}), 200
    else:
        return jsonify({"error": "Task not found"}), 404


@app.route('/export_html', methods=['POST'])
def export_static_html():
    os.makedirs('download', exist_ok=True)
    output_path = os.path.join('download', 'tasklist.html')
    generate_task_html_from_json(json_path=TASKS_JSON_PATH, output_path=output_path)
    return send_file(output_path, as_attachment=True) if os.path.exists(output_path) else ("Failed to generate HTML", 500)

@app.route('/delete_task', methods=['POST'])
def delete_task():
    data = request.get_json()
    task_id = data.get("id")
    tasks = load_tasks()
    found = False
    for t in tasks:
        if t.get("id") == task_id:
            t["status"] = "deleted"
            found = True
            break
    if found:
        save_tasks(tasks)
        return jsonify({"message": "Task marked as deleted"}), 200
    return jsonify({"error": "Task not found"}), 404

@app.route('/restore_task', methods=['POST'])
def restore_task():
    data = request.get_json()
    task_id = data.get("id")
    tasks = load_tasks()
    restored = False
    for t in tasks:
        if t.get("id") == task_id and t.get("status") == "deleted":
            t["status"] = "to do"
            restored = True
            break
    if restored:
        save_tasks(tasks)
        return jsonify({"message": "Task restored"}), 200
    return jsonify({"error": "Task not found or not deleted"}), 404

@app.route('/edit_task', methods=['POST'])
def edit_task():
    data = request.get_json()
    task_id = data.get("id")
    updates = data.get("updates", {})

    # 防止 updates 中不小心带入 id 字段，覆盖了原来的 task["task"]
    updates.pop("id", None)

    tasks = load_tasks()
    found = False
    for task in tasks:
        if task.get("id") == task_id:
            task.update(updates)
            found = True
            break

    if found:
        save_tasks(tasks)
        return jsonify({"message": "Task updated"}), 200
    return jsonify({"error": "Task not found"}), 404


@app.route('/merge_tasks', methods=['POST'])
def merge_tasks():
    data = request.get_json()
    task_ids = data.get("id", [])
    merged_task = data.get("merged_task", {})
    if len(task_ids) < 2 or not merged_task:
        return jsonify({"error": "Need at least two tasks and a merged task definition"}), 400
    tasks = load_tasks()
    kept_tasks = []
    for t in tasks:
        if t.get("id") in task_ids:
            continue
        kept_tasks.append(t)
    kept_tasks.append(merged_task)
    save_tasks(kept_tasks)
    return jsonify({"message": "Tasks merged"}), 200

@app.route('/delete_forever', methods=['POST'])
def delete_forever():
    data = request.get_json()
    task_id = data.get("id")
    tasks = load_tasks()
    filtered_tasks = [t for t in tasks if t.get("id") != task_id]
    if len(filtered_tasks) == len(tasks):
        return jsonify({"error": "Task not found"}), 404
    save_tasks(filtered_tasks)
    return jsonify({"message": "Task permanently deleted"}), 200

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json()
    task_text = data.get("task", "").strip()
    if not task_text:
        return jsonify({"error": "Task name is required"}), 400

    new_task = {
        "task": task_text,
        "due_date": data.get("due_date", ""),
        "priority": data.get("priority", "").lower(),
        "assigner": data.get("assigner", ""),
        "comments": data.get("comments", "")
    }

    append_tasks([new_task])
    return jsonify({"message": "Task added"}), 200

@app.route('/get_health_status', methods=['GET'])
def get_health_status():
    try:
        result = get_today_health_goals()
        return jsonify({"health_goals": result}), 200  # ✅ 用 dict 包裹
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# task_status_api.py 中的 update_health_goal 路由示例
@app.route("/update_health_goal", methods=["POST"])
def update_health_goal():
    try:
        content = request.get_json()
        goal_index = int(content.get("goal_index"))
        done = content.get("done")

        print(f"[DEBUG] Updating health goal index {goal_index} to {done}")
        success = update_health_status(goal_index, done)

        if success:
            return jsonify({"status": "ok"}), 200
        else:
            return jsonify({"status": "failed", "reason": "index out of range"}), 400
    except Exception as e:
        print(f"[ERROR] update_health_goal failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/get_happiness_today")
def get_happiness_today():
    from dailylog.happiness_engine import get_today_happiness_task, initialize_today_happiness_task

    refresh = request.args.get("refresh", "false").lower() == "true"

    if refresh:
        task = initialize_today_happiness_task()
    else:
        task = get_today_happiness_task()
        if not task:
            task = initialize_today_happiness_task()

    return jsonify(task)

@app.route("/update_happiness_entry", methods=["POST"])
def update_happiness_entry():
    try:
        from dailylog.happiness_engine import update_today_happiness_reflection
        from utils.constants import IMAGE_DIR
        from werkzeug.utils import secure_filename
        import datetime

        # 确保 IMAGE_DIR 存在（如 static/images）
        os.makedirs(IMAGE_DIR, exist_ok=True)

        # 读取文字反思内容
        reflection = request.form.get("reflection", "").strip()

        # 处理上传图片
        image = request.files.get("photo")
        image_path = ""

        if image:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
            ext = os.path.splitext(image.filename)[1] or ".jpg"
            filename = secure_filename(f"{timestamp}{ext}")

            # 保存图片到 IMAGE_DIR
            abs_path = os.path.join(IMAGE_DIR, filename)
            image.save(abs_path)

            # 转换为前端可访问的相对路径（static/images/xxx.jpg）
            rel_path = os.path.relpath(abs_path, start="static").replace("\\", "/")
            image_path = f"static/{rel_path}"

        # 写入日志
        update_today_happiness_reflection(reflection=reflection, image_path=image_path)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000)
