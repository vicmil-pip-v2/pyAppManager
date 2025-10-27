from flask import Flask, jsonify, request, render_template
import os
import sys
import pathlib
import re
from functools import wraps

# Add project paths
sys.path.append(str(pathlib.Path(__file__).resolve().parents[0]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[4]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[5]))

from vicmil_pip.lib.pyUtil import *
from vicmil_pip.lib.pyAppManager.app_manager_util import *
import vicmil_pip.lib.pyAppManager.flask_routes_util as flask_util

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
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "auth_token.txt")

app = Flask(__name__, template_folder="templates")
conf_file = "/etc/nginx/conf.d/example.conf"
local_conf_json_path = get_directory_path(__file__) + "/local_conf.json"

flask_util.setup_app_manager_routes(app=app, APP_DIR=APP_DIR, PID_DIR=PID_DIR, LOG_DIR=LOG_DIR, SSH_KEY_PATH=SSH_KEY_PATH, APP_REPO_URL=APP_REPO_URL, TOKEN_FILE=TOKEN_FILE)
flask_util.setup_nginx_manager_routes(app=app, conf_file_path=conf_file, local_conf_json_path=local_conf_json_path, ssl_cert_path=None, server_domain="localhost", TOKEN_FILE=TOKEN_FILE)

if __name__ == "__main__":
    # Fetch all the apps and kill them
    apps = list_installed_apps(APP_DIR)
    for my_app in apps:
        stop_app(PID_DIR, my_app)

    # Run locally on 127.0.0.1
    app.run(host="127.0.0.1", port=5002, debug=False)
