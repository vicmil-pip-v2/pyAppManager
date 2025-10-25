from flask import Flask, jsonify, request, render_template
import os
import sys
import pathlib
import re

# Add project paths
sys.path.append(str(pathlib.Path(__file__).resolve().parents[0]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[4]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[5]))

from vicmil_pip.lib.pyUtil import *
from vicmil_pip.lib.pyAppRepoManager.app_manager_util import *

# Ensure SSH keys exist
ssh_dir = get_directory_path(__file__) + "/.ssh"
if not os.path.exists(ssh_dir):
    generate_ssh_keypair(save_dir=ssh_dir)

# Configuration
APP_DIR = get_directory_path(__file__) + "/apps"
PID_DIR = get_directory_path(__file__) + "/pid"
LOG_DIR = get_directory_path(__file__) + "/logs"
SSH_KEY_PATH = ssh_dir + "/id_ed25519"
APP_REPO_URL = "git@github.com:vicmil-work/private-apps.git"

app = Flask(__name__, template_folder="templates")


def verify_app_name(app_name):
    """
    Verify that app_name only consists of:
    - lowercase letters (a-z)
    - uppercase letters (A-Z)
    - numbers (0-9)
    - underscores (_)
    - dashes (-)
    """
    if re.fullmatch(r"[A-Za-z0-9_-]+", app_name):
        return True
    else:
        raise ValueError(
            "Invalid app name. Only letters, numbers, underscores, and dashes are allowed."
        )


# ====== API ROUTES ======
@app.route("/apps", methods=["GET"])
def list_apps():
    try:
        apps = list_installed_apps(APP_DIR)
        return jsonify({"apps": apps})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/apps/<app_name>/start", methods=["POST"])
def start(app_name):
    try:
        verify_app_name(app_name)
        print("start app")
        start_app(APP_DIR, PID_DIR, LOG_DIR, app_name)
        print(app_name, "started")
        return jsonify({"message": f"{app_name} started."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/apps/<app_name>/stop", methods=["POST"])
def stop(app_name):
    try:
        verify_app_name(app_name)
        stop_app(PID_DIR, app_name)
        return jsonify({"message": f"{app_name} stopped."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/apps/<app_name>/status", methods=["GET"])
def status(app_name):
    verify_app_name(app_name)
    running = is_app_running(PID_DIR, app_name)
    usage = get_app_memory_and_cpu_usage(PID_DIR, app_name) if running else None
    return jsonify({"app_name": app_name, "running": running, "usage": usage})

@app.route("/system/status", methods=["GET"])
def system_status():
    return jsonify(get_computer_memory_and_cpu_usage())

@app.route("/apps/<app_name>/clone", methods=["POST"])
def clone_app(app_name):
    repo_url = APP_REPO_URL
    try:
        verify_app_name(app_name)
        clone_app_from_repo(APP_DIR, repo_url, SSH_KEY_PATH, app_name)
        return jsonify({"message": f"{app_name} cloned."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/apps/<app_name>/pull", methods=["POST"])
def pull_app(app_name):
    try:
        verify_app_name(app_name)
        stop_app(PID_DIR, app_name)
        pull_app_from_repo(APP_DIR, SSH_KEY_PATH, app_name)
        return jsonify({"message": f"{app_name} updated."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/remote_apps", methods=["GET"])
def remote_apps():
    """
    List branches (apps) from the hard-coded remote repo.
    """
    try:
        apps = list_apps_in_repo(APP_REPO_URL, SSH_KEY_PATH)
        return jsonify({"remote_apps": apps})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ====== FRONTEND ======
@app.route("/")
def dashboard():
    """Render dashboard HTML page"""
    return render_template("index.html")


if __name__ == "__main__":
    # Fetch all the apps and kill them
    apps = list_installed_apps(APP_DIR)
    for my_app in apps:
        stop_app(PID_DIR, my_app)

    # Run locally on 127.0.0.1
    app.run(host="127.0.0.1", port=5002, debug=False)
