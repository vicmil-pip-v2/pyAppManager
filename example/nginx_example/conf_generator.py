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
from vicmil_pip.lib.pyAppManager.nginx_util import *

# Example usage
builder = NginxConfigBuilder()

server1 = builder.add_server(
    server_name="localhost", # example.com
    #ssl_cert="/etc/letsencrypt/live/example.com/fullchain.pem",
    #ssl_key="/etc/letsencrypt/live/example.com/privkey.pem"
)
server1.add_redirect_location("/api", "https://github.com")
server1.add_websocket_location("/", 5002)


# Save config directly to conf.d and reload Nginx
conf_file = builder.save_to_file("/etc/nginx/conf.d/example.conf")
conf_file = builder.save_to_file(get_directory_path(__file__) + "/example.conf")

with open(get_directory_path(__file__) + "/builder_config.json", "w+") as file:
    file.write(builder.to_json())

builder.reload_nginx()
