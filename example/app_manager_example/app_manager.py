import sys
import pathlib
import time

sys.path.append(str(pathlib.Path(__file__).resolve().parents[0]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[4]))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[5]))

from vicmil_pip.lib.pyUtil import *
from vicmil_pip.lib.pyAppManager.app_manager_util import *

print("Setting up ssh keys")

ssh_dir = get_directory_path(__file__) + "/.ssh"
if not os.path.exists(ssh_dir):
    generate_ssh_keypair(save_dir=ssh_dir)

ssh_private_key_path = ssh_dir + "/id_ed25519"
app_repo_url = "git@github.com:vicmil-work/private-apps.git"
app_dir = get_directory_path(__file__) + "/apps"
log_dir = get_directory_path(__file__) + "/logs"
pid_dir = get_directory_path(__file__) + "/pid"

os.makedirs(app_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)
os.makedirs(pid_dir, exist_ok=True)

remote_apps_list = list_apps_in_repo(repo_url=app_repo_url, ssh_private_key_path=ssh_private_key_path)

print(remote_apps_list)

local_apps_list = list_installed_apps(app_dir=app_dir)

print(local_apps_list)

clone_app_from_repo(app_dir=app_dir, repo_url=app_repo_url, ssh_private_key_path=ssh_private_key_path, app_name="hello_world")

print("Starting app")
start_app(app_dir=app_dir, pid_dir=pid_dir, log_dir=log_dir, app_name="hello_world")

app_footprint = get_app_memory_and_cpu_usage(pid_dir=pid_dir, app_name="hello_world")

print(app_footprint)

stop_app(pid_dir=pid_dir, app_name="hello_world")
stop_app(pid_dir=pid_dir, app_name="hello_world2")