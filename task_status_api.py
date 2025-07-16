from flask import Flask, request, jsonify, render_template, make_response, send_file
from flask_cors import CORS
from task_storage.task_status_updater import update_task_status
from utils.html_generator import generate_task_html_from_json
from utils.constants import TASKS_JSON_PATH
import json
import os
from datetime import datetime

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
    task_name = data.get('task')
    new_status = data.get('status')
    if not task_name or not new_status:
        return jsonify({"error": "Missing 'task' or 'status' in request"}), 400
    success = update_task_status(task_name, new_status)
    return jsonify({"message": "Status updated" if success else "Task not found"}), 200 if success else 404

@app.route('/export_html', methods=['POST'])
def export_static_html():
    os.makedirs('download', exist_ok=True)
    output_path = os.path.join('download', 'tasklist.html')
    generate_task_html_from_json(json_path=TASKS_JSON_PATH, output_path=output_path)
    return send_file(output_path, as_attachment=True) if os.path.exists(output_path) else ("Failed to generate HTML", 500)

@app.route('/delete_task', methods=['POST'])
def delete_task():
    data = request.get_json()
    task_name = data.get("task")
    tasks = load_tasks()
    found = False
    for t in tasks:
        if t.get("task") == task_name:
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
    task_name = data.get("task")
    tasks = load_tasks()
    restored = False
    for t in tasks:
        if t.get("task") == task_name and t.get("status") == "deleted":
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
    task_name = data.get("task")
    updates = data.get("updates", {})
    if not task_name or not updates:
        return jsonify({"error": "Missing task name or updates"}), 400

    tasks = load_tasks()
    updated = False
    for t in tasks:
        if t.get("task") == task_name:
            t.update(updates)
            if "due_date" in updates:
                t["deadline"] = updates["due_date"]
            updated = True
            break
    if updated:
        save_tasks(tasks)
        return jsonify({"message": "Task updated"}), 200
    return jsonify({"error": "Task not found"}), 404

@app.route('/merge_tasks', methods=['POST'])
def merge_tasks():
    data = request.get_json()
    task_names = data.get("tasks", [])
    merged_task = data.get("merged_task", {})
    if len(task_names) < 2 or not merged_task:
        return jsonify({"error": "Need at least two tasks and a merged task definition"}), 400
    tasks = load_tasks()
    kept_tasks = []
    for t in tasks:
        if t.get("task") in task_names:
            continue
        kept_tasks.append(t)
    kept_tasks.append(merged_task)
    save_tasks(kept_tasks)
    return jsonify({"message": "Tasks merged"}), 200

@app.route('/delete_forever', methods=['POST'])
def delete_forever():
    data = request.get_json()
    task_name = data.get("task")
    tasks = load_tasks()
    filtered_tasks = [t for t in tasks if t.get("task") != task_name]
    if len(filtered_tasks) == len(tasks):
        return jsonify({"error": "Task not found"}), 404
    save_tasks(filtered_tasks)
    return jsonify({"message": "Task permanently deleted"}), 200

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json()
    if not data or not data.get("task"):
        return jsonify({"error": "Task content is missing"}), 400

    task_obj = {
        "task": data["task"],
        "due_date": data.get("due_date"),
        "deadline": data.get("due_date"),
        "priority": data.get("priority", "normal"),
        "assigner": data.get("assigner", "User"),
        "comments": data.get("comments", ""),
        "status": "to do",
        "email_content": None
    }

    tasks = load_tasks()
    tasks.append(task_obj)
    save_tasks(tasks)
    return jsonify({"message": "Task added"}), 200

if __name__ == '__main__':
    app.run(port=5000)