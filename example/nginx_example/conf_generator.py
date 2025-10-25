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
from vicmil_pip.lib.pyAppRepoManager.nginx_util import *

# Example usage
builder = NginxConfigBuilder()

server1 = builder.add_server(
    server_name="_", # example.com
    use_http=True,
    #use_https=True,
    #ssl_cert="/etc/letsencrypt/live/example.com/fullchain.pem",
    #ssl_key="/etc/letsencrypt/live/example.com/privkey.pem"
)
server1.add_location("/", 5002, websocket=True)
server1.add_location("/api", 10001)

# Save config directly to conf.d and reload Nginx
conf_file = builder.save_to_file("/etc/nginx/conf.d/example.conf")
conf_file = builder.save_to_file(get_directory_path(__file__) + "/example.conf")
builder.reload_nginx()
