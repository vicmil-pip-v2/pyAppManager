import sys
import pathlib
import os

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2])) 

import git_util

def get_directory_path(__file__in, up_directories=0):
    return str(pathlib.Path(__file__in).parents[up_directories].resolve()).replace("\\", "/")

repo_url = "git@github.com:02vicmil/private-apps.git" # Change to your repo

ssh_key_dir = get_directory_path(__file__) + "/.ssh"

if not os.path.exists(ssh_key_dir):
    git_util.generate_ssh_keypair(ssh_key_dir)
    print(f"SSH key generated in {ssh_key_dir}, you must set the public key in github/bitbucket repo for the code to have access")
    exit(0)

with open(ssh_key_dir + "/id_ed25519") as file:
    private_ssh_deploy_key = file.read()

clone_dir = get_directory_path(__file__) + "/clone_dir"

branch = "hello_world"

if not os.path.exists(clone_dir):
    git_util.clone_private_repo(repo_url, private_ssh_deploy_key, clone_dir, branch)
else:
    git_util.pull_latest_changes(clone_dir, private_ssh_deploy_key)
