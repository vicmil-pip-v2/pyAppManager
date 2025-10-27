from flask import Flask, jsonify, request, render_template, Blueprint
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
from vicmil_pip.lib.pyAppRepoManager.app_manager_util import *
from vicmil_pip.lib.pyAppRepoManager.nginx_util import NginxConfigBuilder

import secrets

import json


def setup_app_manager_routes(app, APP_DIR: str, PID_DIR: str, LOG_DIR: str, SSH_KEY_PATH: str, APP_REPO_URL: str, TOKEN_FILE: str, namespace="/", ):
    def verify_app_name(app_name):
        """
        Verify that app_name only consists of:
        - lowercase letters (a-z)
        - uppercase letters (A-Z)
        - numbers (0-9)
        - underscores (_)
        - dashes (-)
        """
        if len(app_name) > 30:
            raise ValueError(
                "Invalid app name. Maximum 30 letters allowed."
            )
        if not re.fullmatch(r"[A-Za-z0-9_-]+", app_name):
            raise ValueError(
                "Invalid app name. Only letters, numbers, underscores, and dashes are allowed."
            )
        
        return True

    def load_or_create_token():
        """Generate a random token if it doesn't exist, else load from file."""
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                token = f.read().strip()
                if token:
                    return token

        # Generate a secure random token
        token = secrets.token_hex(32)  # 64-character hex token
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        print(f"[INFO] Auth token generated and saved to: {TOKEN_FILE}")
        return token

    AUTH_TOKEN = load_or_create_token()

    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get("Authorization")

            if not token:
                return jsonify({"error": "Missing Authorization header"}), 401

            # Support "Bearer <token>" or plain token
            if token.startswith("Bearer "):
                token = token.split("Bearer ")[1]

            if token != AUTH_TOKEN:
                return jsonify({"error": "Invalid or expired token"}), 403

            return f(*args, **kwargs)
        return decorated

    templates_folder = os.path.join(os.path.dirname(__file__), "templates")
    bp = Blueprint("apps_manager", __name__, url_prefix=namespace, template_folder=templates_folder)

    # ====== API ROUTES ======
    @bp.route("/apps", methods=["GET"])
    @require_auth
    def list_apps():
        try:
            apps = list_installed_apps(APP_DIR)
            return jsonify({"apps": apps})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @bp.route("/apps/<app_name>/start", methods=["POST"])
    @require_auth
    def start(app_name):
        try:
            verify_app_name(app_name)
            print("start app")
            start_app(APP_DIR, PID_DIR, LOG_DIR, app_name)
            print(app_name, "started")
            return jsonify({"message": f"{app_name} started."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @bp.route("/apps/<app_name>/stop", methods=["POST"])
    @require_auth
    def stop(app_name):
        try:
            verify_app_name(app_name)
            stop_app(PID_DIR, app_name)
            return jsonify({"message": f"{app_name} stopped."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @bp.route("/apps/<app_name>/status", methods=["GET"])
    @require_auth
    def status(app_name):
        verify_app_name(app_name)
        running = is_app_running(PID_DIR, app_name)
        usage = get_app_memory_and_cpu_usage(PID_DIR, app_name) if running else None
        return jsonify({"app_name": app_name, "running": running, "usage": usage})

    @bp.route("/system/status", methods=["GET"])
    @require_auth
    def system_status():
        return jsonify(get_computer_memory_storage_and_cpu_usage())

    @bp.route("/apps/<app_name>/clone", methods=["POST"])
    @require_auth
    def clone_app(app_name):
        repo_url = APP_REPO_URL
        try:
            verify_app_name(app_name)
            clone_app_from_repo(APP_DIR, repo_url, SSH_KEY_PATH, app_name)
            return jsonify({"message": f"{app_name} cloned."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @bp.route("/apps/<app_name>/pull", methods=["POST"])
    @require_auth
    def pull_app(app_name):
        try:
            verify_app_name(app_name)
            stop_app(PID_DIR, app_name)
            pull_app_from_repo(APP_DIR, SSH_KEY_PATH, app_name)
            return jsonify({"message": f"{app_name} updated."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    @bp.route("/remote_apps", methods=["GET"])
    @require_auth
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
    @bp.route("/")
    def dashboard():
        """Render dashboard HTML page"""
        return render_template("index.html")


    @bp.route("/login")
    def login():
        return render_template("login.html")
    
    app.register_blueprint(bp)


def setup_nginx_manager_routes(app, conf_file_path: str, local_conf_json_path: str, ssl_cert_path: str, server_domain: str, TOKEN_FILE: str, namespace="/nginx", http_only=True):
    def load_or_create_token():
        """Generate a random token if it doesn't exist, else load from file."""
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                token = f.read().strip()
                if token:
                    return token
        token = secrets.token_hex(32)
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        print(f"[INFO] Auth token generated and saved to: {TOKEN_FILE}")
        return token

    AUTH_TOKEN = load_or_create_token()

    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get("Authorization")
            if not token:
                return jsonify({"error": "Missing Authorization header"}), 401
            if token.startswith("Bearer "):
                token = token.split("Bearer ")[1]
            if token != AUTH_TOKEN:
                return jsonify({"error": "Invalid or expired token"}), 403
            return f(*args, **kwargs)
        return decorated

    templates_folder = os.path.join(os.path.dirname(__file__), "templates")
    bp = Blueprint("nginx_manager", __name__, url_prefix=namespace, template_folder=templates_folder)

    # ---------------------------------------------------
    # 1. Home Page
    # ---------------------------------------------------
    @bp.route("/", methods=["GET"])
    def home():
        """Simple landing page."""
        return render_template("nginx_home.html", domain=server_domain)

    # ---------------------------------------------------
    # 2. Get Local Config JSON
    # ---------------------------------------------------
    @bp.route("/conf", methods=["GET"])
    @require_auth
    def get_conf():
        """
        Return the current configuration.
        If no file exists, create a default one and return it.
        """
        default_conf = {
            "routes": [
                {"route": "/", "port": 10001, "websocket": False}
            ]
        }

        # Create default config file if missing
        if not os.path.exists(local_conf_json_path):
            try:
                os.makedirs(os.path.dirname(local_conf_json_path), exist_ok=True)
                with open(local_conf_json_path, "w") as f:
                    json.dump(default_conf, f, indent=4)
                print(f"[INFO] Created default nginx config at {local_conf_json_path}")
            except Exception as e:
                return jsonify({"error": f"Failed to create default config: {str(e)}"}), 500

            return jsonify(default_conf), 201  # Created

        # Load and return existing config
        try:
            with open(local_conf_json_path, "r") as f:
                return jsonify(json.load(f))
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON in configuration"}), 500
        except Exception as e:
            return jsonify({"error": f"Failed to read config: {str(e)}"}), 500

    # ---------------------------------------------------
    # 3. Update Local Config JSON
    # ---------------------------------------------------
    @bp.route("/conf", methods=["POST"])
    @require_auth
    def update_conf():
        """
        Update the configuration JSON file.
        Ensures all routes use ports in the 10000–15000 range.
        """
        try:
            new_conf = request.get_json(force=True)
        except Exception as e:
            return jsonify({"error": f"Invalid JSON body: {e}"}), 400

        if not isinstance(new_conf, dict) or "routes" not in new_conf:
            return jsonify({"error": "Config must contain a 'routes' list"}), 400

        routes = new_conf.get("routes", [])
        if not isinstance(routes, list):
            return jsonify({"error": "'routes' must be a list"}), 400

        # Validate each route
        for i, route in enumerate(routes):
            if not isinstance(route, dict):
                return jsonify({"error": f"Route #{i+1} must be an object"}), 400

            port = route.get("port")
            if not isinstance(port, int):
                return jsonify({"error": f"Route #{i+1}: 'port' must be an integer"}), 400

            if not (10000 <= port <= 15000):
                return jsonify({"error": f"Route #{i+1}: Port {port} out of allowed range (10000–15000)"}), 400

            if not route.get("route"):
                return jsonify({"error": f"Route #{i+1}: Missing 'route' value"}), 400

            if "websocket" in route and not isinstance(route["websocket"], bool):
                return jsonify({"error": f"Route #{i+1}: 'websocket' must be a boolean"}), 400

        # Save config
        try:
            os.makedirs(os.path.dirname(local_conf_json_path), exist_ok=True)
            with open(local_conf_json_path, "w") as f:
                json.dump(new_conf, f, indent=4)
        except Exception as e:
            return jsonify({"error": f"Failed to write config: {str(e)}"}), 500

        return jsonify({"message": "Configuration updated successfully"})

    # ---------------------------------------------------
    # 4. Build Config + Reload Nginx
    # ---------------------------------------------------
    @bp.route("/build", methods=["POST"])
    @require_auth
    def build_and_apply():
        """Build nginx.conf from routes using NginxConfigBuilder, then reload nginx."""
        if not os.path.exists(local_conf_json_path):
            return jsonify({"error": "No config file found"}), 404

        try:
            with open(local_conf_json_path, "r") as f:
                conf_data = json.load(f)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON in config"}), 500

        routes = conf_data.get("routes", [])
        if not routes:
            return jsonify({"error": "No routes defined"}), 400

        try:
            # Create builder
            builder = NginxConfigBuilder()

            # Add main server block (either HTTP or HTTPS)
            server = builder.add_server(
                server_name=server_domain,
                use_http=http_only,
                use_https=not http_only,
                ssl_cert=ssl_cert_path if not http_only else None,
                ssl_key=ssl_cert_path.replace(".crt", ".key") if not http_only else None
            )

            # Add routes
            for entry in routes:
                route = entry.get("route", "/")
                port = entry.get("port")
                websocket = entry.get("websocket", False)

                if port is None:
                    return jsonify({"error": f"Route {route} missing port"}), 400

                if websocket:
                    server.add_websocket_location(route, port)
                else:
                    server.add_proxy_location(route, port)

            # Generate + Save + Reload
            builder.save_to_file(conf_file_path)
            builder.reload_nginx()

            return jsonify({"message": "Nginx configuration built and reloaded successfully."})
        except subprocess.CalledProcessError:
            return jsonify({"error": "Nginx configuration test failed"}), 500
        except Exception as e:
            return jsonify({"error": f"Failed to build nginx config: {e}"}), 500

    # Register blueprint
    app.register_blueprint(bp)


if __name__ == "__main__":
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

    # Fetch all the apps and kill them
    apps = list_installed_apps(APP_DIR)
    for my_app in apps:
        stop_app(PID_DIR, my_app)

    setup_app_manager_routes(app=app, APP_DIR=APP_DIR, PID_DIR=PID_DIR, LOG_DIR=LOG_DIR, SSH_KEY_PATH=SSH_KEY_PATH, APP_REPO_URL=APP_REPO_URL)

    # Run locally on 127.0.0.1
    app.run(host="127.0.0.1", port=5002, debug=False)
