import os
import subprocess
import json

class NginxConfigBuilder:
    def __init__(self):
        self.servers = []

    def add_server(self, server_name="_", ssl_cert=None, ssl_key=None):
        server = NginxServer(server_name, ssl_cert, ssl_key)
        self.servers.append(server)
        return server

    def generate_full_config(self):
        config = ""
        for server in self.servers:
            config += server.generate_config()
        return config

    def save_to_file(self, filepath="/etc/nginx/conf.d/generated.conf"):
        """
        Save the generated config to a file.
        """
        config = self.generate_full_config()
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(config)
        print(f"Nginx configuration saved to {filepath}")
        return filepath

    def reload_nginx(self):
        """
        Test and reload Nginx safely.
        """
        try:
            subprocess.run(["nginx", "-t"], check=True)  # Test config
            subprocess.run(["systemctl", "reload", "nginx"], check=True)
            print("Nginx reloaded successfully.")
        except subprocess.CalledProcessError:
            print("Error: Nginx configuration test failed. Not reloading.")


    # --- JSON Conversion ---
    def to_json(self) -> str:
        """Serialize the builder (and all servers) to a JSON string."""
        data = {
            "servers": [server.to_dict() for server in self.servers]
        }
        return json.dumps(data, indent=4)

    @classmethod
    def from_json(cls, json_str: str) -> "NginxConfigBuilder":
        """Recreate a builder from a JSON string."""
        data = json.loads(json_str)
        builder = cls()
        for server_data in data.get("servers", []):
            server = NginxServer.from_dict(server_data)
            builder.servers.append(server)
        return builder


class NginxServer:
    def __init__(self, server_name="_", ssl_cert=None, ssl_key=None):
        # Will automatically use https if ssl_cert and ssl_key is provided
        self.server_name = server_name
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self.locations = {}  # key = route, value = dict with type and config

    # --- Location Adders ---
    def add_proxy_location(self, route: str, port: int):
        """Add a standard HTTP proxy location."""
        self.locations[route] = {"type": "proxy", "port": port, "websocket": False}

    def add_websocket_location(self, route: str, port: int):
        """Add a WebSocket proxy location."""
        self.locations[route] = {"type": "websocket", "port": port, "websocket": True}

    def add_redirect_location(self, route: str, redirect_url: str):
        """Add a location that redirects to a URL."""
        self.locations[route] = {"type": "redirect", "redirect_url": redirect_url}

    # --- Location Block Generator ---
    def _generate_location_block(self, route, cfg):
        block = f"    location {route} {{\n"
        if cfg["type"] == "redirect":
            block += f"        return 301 {cfg['redirect_url']};\n"
        else:
            block += f"        proxy_pass http://127.0.0.1:{cfg['port']};\n"
            block += f"        proxy_set_header X-Real-IP $remote_addr;\n"
            block += f"        proxy_set_header Host $host;\n"
            block += f"        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
            if cfg.get("websocket"):
                block += f"        proxy_http_version 1.1;\n"
                block += f"        proxy_set_header Upgrade $http_upgrade;\n"
                block += f"        proxy_set_header Connection \"upgrade\";\n"
                #block += f"        proxy_set_header Origin $http_origin;\n"
        block += f"    }}\n"
        return block

    # --- Server Block Generator ---
    def _generate_server_block(self, listen_port, ssl=False, redirect_to_https=False):
        server_block = f"server {{\n"
        server_block += f"    listen {listen_port}"
        if ssl:
            server_block += " ssl"
        server_block += ";\n"
        server_block += f"    server_name {self.server_name};\n\n"
        #server_block += f"    server_name_in_redirect off;\n"

        if ssl:
            if not self.ssl_cert or not self.ssl_key:
                raise ValueError("SSL certificate and key must be provided for HTTPS")
            server_block += f"    ssl_certificate {self.ssl_cert};\n"
            server_block += f"    ssl_certificate_key {self.ssl_key};\n\n"

        if redirect_to_https:
            server_block += "    location / {\n"
            server_block += "       return 301 https://$host$request_uri;\n"
            server_block += "    }\n"
        else:
            for route, cfg in self.locations.items():
                server_block += self._generate_location_block(route, cfg)

        server_block += "}\n\n"
        return server_block

    # --- Full Config Generator ---
    def generate_config(self):
        config = ""
        use_https = self.ssl_key is not None

        # Generate http code
        http_port = 80 if self.server_name != "localhost" else 8000
        redirect_to_https = use_https
        config += self._generate_server_block(http_port, ssl=False, redirect_to_https=redirect_to_https)

        # Generate https code
        if use_https:
            config += self._generate_server_block(443, ssl=True)
        return config
    
    # --- JSON Conversion ---
    def to_dict(self) -> dict:
        """Convert this server to a serializable dict."""
        return {
            "server_name": self.server_name,
            "ssl_cert": self.ssl_cert,
            "ssl_key": self.ssl_key,
            "locations": self.locations
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NginxServer":
        """Recreate a server from a dict."""
        server = cls(
            server_name=data.get("server_name", "_"),
            ssl_cert=data.get("ssl_cert"),
            ssl_key=data.get("ssl_key"),
        )
        server.locations = data.get("locations", {})
        return server