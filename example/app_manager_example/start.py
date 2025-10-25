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

if __name__ == "__main__":
    # start_file_path = get_directory_path(__file__) + "/app_manager.py"
    start_file_path = get_directory_path(__file__) + "/app_manager_flask.py"
    venv_path = get_directory_path(__file__) + "/venv"
    requirements_file_path = get_directory_path(__file__) + "/requirements.txt"
    url = "http://127.0.0.1:5002"

    open_webbrowser(url)

    if not os.path.exists(venv_path):
        python_virtual_environment(venv_path)

    pip_install_requirements_file_in_virtual_environment(
        env_directory_path=venv_path,
        requirements_file_path=requirements_file_path
    )

    new_process = None
    try:
        new_process = invoke_python_file_using_subprocess(venv_path, start_file_path)
        while True:
            time.sleep(1)
    finally:
        if new_process:
            new_process.kill()

    
        
