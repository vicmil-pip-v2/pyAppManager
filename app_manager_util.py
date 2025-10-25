import sys
import pathlib
import os
import psutil
import subprocess
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from vicmil_pip.lib.pyUtil import get_directory_path
from vicmil_pip.lib.pyAppRepoManager.git_util import clone_repo_using_ssh_key, pull_latest_changes_using_ssh_key, generate_ssh_keypair, list_branches_using_ssh_key
from vicmil_pip.lib.pyUtil import *


def run_python_app_command(python_path, app_file, log_file, pid_file):
    if platform.system() == "Windows":
        # PowerShell command
        command = f'Start-Process -NoNewWindow -FilePath "{python_path}" -ArgumentList "-u","{app_file}" -RedirectStandardOutput "{log_file}" -RedirectStandardError "{log_file}" -PassThru | ForEach-Object {{ $_.Id > "{pid_file}" }}'
    else:
        # Linux/macOS command
        command = f'nohup "{python_path}" -u "{app_file}" >> "{log_file}" 2>&1 & echo $! > "{pid_file}"'
    
    print("Running command:", command)
    os.system(command)


def start_app(app_dir: str, pid_dir: str, log_dir: str, app_name: str):
    """
    Starts a Python app from a given directory.
    - Creates virtualenv if requirements.txt exists
    - Installs dependencies
    - Runs app.py in the background
    - Saves PID to pid_dir/app_name_pid.txt
    """
    app_path = os.path.join(app_dir, app_name)
    venv_path = os.path.join(app_path, "venv")
    requirements_path = os.path.join(app_path, "requirements.txt")
    app_file = os.path.join(app_path, "app.py")
    pid_file = os.path.join(pid_dir, f"{app_name}_pid.txt")
    log_file = os.path.join(log_dir, f"{app_name}.log")

    if is_app_running(pid_dir=pid_dir, app_name=app_name):
        print("Process already started!")
        return

    os.makedirs(pid_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    # 1. Create virtual environment if requirements exist
    if os.path.exists(requirements_path):
        python_virtual_environment(venv_path)
        pip_install_requirements_file_in_virtual_environment(env_directory_path=venv_path, requirements_file_path=requirements_path)

    # 2. Start the app

    python_path = get_python_executable(venv_path)
    run_python_app_command(python_path, app_file, log_file, pid_file)
    print(f"{app_name} started. PID saved to {pid_file}")


def stop_app(pid_dir: str, app_name: str):
    """
    Stops an app by killing its process (and children) based on saved PID.
    """
    pid_file = os.path.join(pid_dir, f"{app_name}_pid.txt")

    if not os.path.exists(pid_file):
        print(f"No PID file found for {app_name}")
        return

    with open(pid_file, "r") as f:
        pid = int(f.read().strip())

    try:
        process = psutil.Process(pid)
        print(f"Stopping {app_name} (PID {pid})...")
        for child in process.children(recursive=True):
            child.kill()
        process.kill()
        process.wait(timeout=5)
        print(f"{app_name} stopped.")
    except psutil.NoSuchProcess:
        print(f"Process {pid} not found.")
    finally:
        if os.path.exists(pid_file):
            os.remove(pid_file)


def is_app_running(pid_dir: str, app_name: str):
    """
    Checks if app is currently running by verifying PID.
    Removes PID file if not running.
    """
    pid_file = os.path.join(pid_dir, f"{app_name}_pid.txt")

    if not os.path.exists(pid_file):
        return False

    with open(pid_file, "r") as f:
        pid = int(f.read().strip())

    if psutil.pid_exists(pid):
        process = psutil.Process(pid)
        if process.is_running():
            return True

    # Cleanup if process not running
    os.remove(pid_file)
    return False


def get_app_memory_and_cpu_usage(pid_dir: str, app_name: str):
    """
    Returns CPU and memory usage for the app if running.
    Example return: {"cpu_percent": 3.2, "memory_mb": 124.5}
    """
    if not is_app_running(pid_dir, app_name):
        print("get_app_memory_and_cpu_usage", "app is not running")
        return None

    pid_file = os.path.join(pid_dir, f"{app_name}_pid.txt")
    with open(pid_file, "r") as f:
        pid = int(f.read().strip())

    process = psutil.Process(pid)
    cpu = process.cpu_percent(interval=0.5)
    mem = process.memory_info().rss / (1024 * 1024)  # MB
    return {"cpu_percent": cpu, "memory_mb": mem}


def list_installed_apps(app_dir: str):
    """
    Returns a list of files and directories in the given path.

    Args:
        app_dir (str): Path to the directory.

    Returns:
        dict: Contains lists of 'files' and 'directories'.
    """
    if not os.path.exists(app_dir):
        raise FileNotFoundError(f"The directory '{app_dir}' does not exist.")
    
    files = []
    directories = []

    for entry in os.listdir(app_dir):
        full_path = os.path.join(app_dir, entry)
        if os.path.isdir(full_path):
            directories.append(entry)
        else:
            files.append(entry)

    return sorted(directories)


def get_computer_memory_and_cpu_usage():
    # CPU usage (percentage)
    cpu_usage = psutil.cpu_percent(interval=1)

    # Memory usage
    memory = psutil.virtual_memory()

    # Return as dictionary
    return {
        "cpu_usage_percent": cpu_usage,
        "memory_usage_percent": memory.percent,
        "total_memory_gb": round(memory.total / (1024 ** 3), 2),
        "used_memory_gb": round(memory.used / (1024 ** 3), 2),
        "available_memory_gb": round(memory.available / (1024 ** 3), 2)
    }


def clone_app_from_repo(app_dir: str, repo_url: str, ssh_private_key_path: str, app_name: str):
    with open(ssh_private_key_path, "r") as file:
        private_ssh_deploy_key = file.read()
    
    clone_dir = app_dir + "/" + app_name
    branch = app_name

    if not os.path.exists(clone_dir):
        clone_repo_using_ssh_key(repo_url, private_ssh_deploy_key, clone_dir, branch)


def pull_app_from_repo(app_dir: str, ssh_private_key_path: str, app_name: str):
    with open(ssh_private_key_path, "r") as file:
        private_ssh_deploy_key = file.read()
    
    repo_dir = app_dir + "/" + app_name
    branch = app_name

    if os.path.exists(repo_dir):
        pull_latest_changes_using_ssh_key(repo_dir, private_ssh_deploy_key, branch)


def list_apps_in_repo(repo_url: str, ssh_private_key_path: str):
    with open(ssh_private_key_path, "r") as file:
        private_ssh_deploy_key = file.read()

    return list_branches_using_ssh_key(repo_url=repo_url, deploy_key=private_ssh_deploy_key)