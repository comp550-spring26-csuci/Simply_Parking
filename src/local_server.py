# local_server.py
# A tiny built-in HTTP server that runs alongside the Tkinter app.
# It serves the success/cancel HTML pages that Stripe redirects the user
# to after they finish paying. Starts automatically on app launch.
#
# Why this exists: Stripe Checkout requires a real success_url. Without
# this server, we'd have to use a placeholder like example.com, which
# looks broken to demo viewers. With it, we get a polished local page
# that looks just like Stripe's own confirmation page.

import http.server
import os
import socketserver
import threading

PORT = 8765


def get_server_url():
    """Base URL where the server is reachable."""
    return f"http://localhost:{PORT}"


def start_server_in_background():
    """Start the HTTP server in a background daemon thread.

    Safe to call multiple times — if port 8765 is already in use, we
    assume the server is already running and return False.

    Returns True if the server started, False otherwise.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(here, "static")

    if not os.path.isdir(static_dir):
        print(f"[local_server] WARNING: static dir not found at {static_dir}")
        return False

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            # silence default logging
            pass

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=static_dir, **kwargs)

    try:
        httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
        httpd.allow_reuse_address = True
    except OSError as e:
        print(f"[local_server] Port {PORT} in use (already running?): {e}")
        return False

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    print(f"[local_server] Serving payment pages at {get_server_url()}")
    return True


if __name__ == "__main__":
    # standalone mode for testing
    start_server_in_background()
    print("Press Ctrl+C to stop.")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\nStopped.")
