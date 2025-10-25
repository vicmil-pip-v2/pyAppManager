import os
import subprocess

class NginxConfigBuilder:
    def __init__(self):
        self.servers = []

    def add_server(self, server_name="_", use_http=True, use_https=False, ssl_cert=None, ssl_key=None):
        server = NginxServer(server_name, use_http, use_https, ssl_cert, ssl_key)
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


class NginxServer:
    def __init__(self, server_name="_", use_http=True, use_https=False, ssl_cert=None, ssl_key=None):
        self.server_name = server_name
        self.use_http = use_http
        self.use_https = use_https
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self.locations = {}

    def add_location(self, route: str, port: int, websocket: bool = False):
        self.locations[route] = {"port": port, "websocket": websocket}

    def _generate_location_block(self, route, port, websocket):
        block = f"    location {route} {{\n"
        block += f"        proxy_pass http://127.0.0.1:{port};\n"
        block += f"        proxy_set_header X-Real-IP $remote_addr;\n"
        block += f"        proxy_set_header Host $host;\n"
        block += f"        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
        if websocket:
            block += f"        proxy_http_version 1.1;\n"
            block += f"        proxy_set_header Upgrade $http_upgrade;\n"
            block += f"        proxy_set_header Connection \"upgrade\";\n"
            block += f"        proxy_set_header Origin $http_origin;\n"
        block += f"    }}\n"
        return block

    def _generate_server_block(self, listen_port, ssl=False, redirect_to_https=False):
        server_block = f"server {{\n"
        server_block += f"    listen {listen_port}"
        if ssl:
            server_block += " ssl"
        server_block += ";\n"
        server_block += f"    server_name {self.server_name};\n\n"

        if ssl:
            if not self.ssl_cert or not self.ssl_key:
                raise ValueError("SSL certificate and key must be provided for HTTPS")
            server_block += f"    ssl_certificate {self.ssl_cert};\n"
            server_block += f"    ssl_certificate_key {self.ssl_key};\n\n"

        if redirect_to_https:
            server_block += "    return 301 https://$host$request_uri;\n"
        else:
            for route, cfg in self.locations.items():
                server_block += self._generate_location_block(route, cfg["port"], cfg["websocket"])
        server_block += "}\n\n"
        return server_block

    def generate_config(self):
        config = ""
        if self.use_http:
            http_port = 80
            if self.server_name == "_":
                http_port = 8000 # For local development

            redirect_to_https = self.use_https
            config += self._generate_server_block(http_port, ssl=False, redirect_to_https=redirect_to_https)
        if self.use_https:
            config += self._generate_server_block(443, ssl=True)
        return config
