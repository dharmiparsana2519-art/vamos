"""Run ¡Vamos! on your own computer.

Open this file in IDLE and press F5. The site opens in your browser.
Press Ctrl+C in the IDLE shell (or close it) to stop the server.
"""
import functools
import http.server
import os
import socketserver
import threading
import webbrowser


class SiteHandler(http.server.SimpleHTTPRequestHandler):
    """Serves the site folder with the right content types and a quiet log."""

    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".wasm": "application/wasm",
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".json": "application/json",
        ".zip": "application/zip",
        ".py": "text/plain; charset=utf-8",
        ".html": "text/html; charset=utf-8",
    }

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError):
            pass  # the browser cancelled a download (e.g. a page reload): nothing to report

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, format, *args):
        pass  # keep the IDLE shell quiet


class SiteServer:
    """Starts a ThreadingTCPServer on port 8000 (or the next free port) and opens the browser."""

    PORTS = range(8000, 8011)

    def __init__(self, folder: str):
        self.folder = folder
        self.httpd = None
        self.url = ""

    def _bind(self):
        socketserver.ThreadingTCPServer.allow_reuse_address = True
        handler = functools.partial(SiteHandler, directory=self.folder)
        for port in self.PORTS:
            try:
                server = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
                server.daemon_threads = True
                return server, port
            except OSError:
                continue
        raise OSError("Ports 8000-8010 are all busy. Close the other server and try again.")

    def start(self) -> None:
        self.httpd, port = self._bind()
        self.url = f"http://localhost:{port}/"
        print("¡Vamos! is running.")
        print(f"  Open {self.url} in your browser (it should open by itself in a second).")
        print("  Leave this window open while you study.")
        print("  To stop: press Ctrl+C here, or close this shell window.")
        threading.Timer(1.0, webbrowser.open, [self.url]).start()
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping… ¡Hasta luego!")
        finally:
            self.httpd.server_close()


if __name__ == "__main__":
    SiteServer(os.path.dirname(os.path.abspath(__file__))).start()
