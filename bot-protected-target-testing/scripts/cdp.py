#!/usr/bin/env python3
"""cdp.py — minimal raw Chrome DevTools Protocol client over websocket.

Why this exists: some targets break Playwright/Puppeteer's own CDP session
(a stray `targetInfo` event for a shared_worker can kill the driver's socket
read loop mid-session on long runs). Driving an already-running real Chrome
over a raw CDP websocket, with no Playwright/Puppeteer driver in the loop,
sidesteps that failure mode entirely.

This is a generic utility (re-created here after the original skill it lived
in was removed from this kit for containing unrelated client-specific data —
see bounty-kit/README.md's sanitization note). Nothing target-specific is
baked in below.

Setup:
    pip install --user websocket-client requests
    # Launch Chrome/Chromium with a remote debug port, e.g.:
    google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/cdp-profile

Usage:
    from cdp import CDP
    c = CDP(port=9222)                  # attaches to the first open tab
    c.navigate("https://example.com")
    c.wait_load()
    html = c.evaluate("document.documentElement.outerHTML")
    cookies = c.get_cookies()
    c.click(100, 200)
    c.close()

CLI usage:
    python cdp.py --port 9222 --navigate https://example.com --eval "document.title"
"""
from __future__ import annotations
import argparse
import json
import sys
import time
import itertools

try:
    import requests
    import websocket  # from websocket-client
except ImportError:
    print("Missing deps. Install with: pip install --user websocket-client requests",
          file=sys.stderr)
    raise


class CDP:
    """Thin synchronous CDP client over a single websocket connection."""

    def __init__(self, port: int = 9222, host: str = "127.0.0.1", target_index: int = 0,
                 timeout: float = 15.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._id_counter = itertools.count(1)

        targets = requests.get(f"http://{host}:{port}/json", timeout=timeout).json()
        pages = [t for t in targets if t.get("type") == "page"]
        if not pages:
            raise RuntimeError(
                f"No open 'page' targets on {host}:{port}. Is Chrome running with "
                f"--remote-debugging-port={port}?"
            )
        target = pages[target_index]
        self.ws_url = target["webSocketDebuggerUrl"]
        self.ws = websocket.create_connection(self.ws_url, timeout=timeout)

        # Enable the domains this helper uses.
        for domain in ("Page", "Runtime", "Network", "Input", "DOM"):
            self._send(f"{domain}.enable")

    # -- low-level -------------------------------------------------------
    def _send(self, method: str, params: dict | None = None) -> dict:
        msg_id = next(self._id_counter)
        payload = {"id": msg_id, "method": method, "params": params or {}}
        self.ws.send(json.dumps(payload))
        return self._wait_for(msg_id)

    def _wait_for(self, msg_id: int, max_wait: float | None = None) -> dict:
        deadline = time.time() + (max_wait if max_wait is not None else self.timeout)
        while time.time() < deadline:
            raw = self.ws.recv()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if data.get("id") == msg_id:
                if "error" in data:
                    raise RuntimeError(f"CDP error on msg {msg_id}: {data['error']}")
                return data.get("result", {})
            # else: an event or a response to another call — ignore and keep waiting
        raise TimeoutError(f"Timed out waiting for response to CDP call id={msg_id}")

    # -- navigation --------------------------------------------------------
    def navigate(self, url: str) -> dict:
        return self._send("Page.navigate", {"url": url})

    def wait_load(self, timeout: float = 15.0) -> None:
        """Poll document.readyState instead of relying on a Page.loadEventFired
        event, since that event can be the one that gets lost on flaky targets."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            state = self.evaluate("document.readyState")
            if state == "complete":
                return
            time.sleep(0.25)
        raise TimeoutError("Page did not reach readyState=complete in time")

    # -- JS execution --------------------------------------------------------
    def evaluate(self, expression: str, await_promise: bool = True):
        result = self._send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": await_promise,
        })
        remote = result.get("result", {})
        if result.get("exceptionDetails"):
            raise RuntimeError(f"JS exception: {result['exceptionDetails']}")
        return remote.get("value")

    def fetch_json(self, url: str, options: str = "{}"):
        """Run fetch() in-page (keeps the page's cookies/origin/CSP context)
        and return the parsed JSON body."""
        expr = f"""
        (async () => {{
            const r = await fetch({json.dumps(url)}, {options});
            const text = await r.text();
            try {{ return JSON.stringify({{status: r.status, body: JSON.parse(text)}}); }}
            catch (e) {{ return JSON.stringify({{status: r.status, body: text}}); }}
        }})()
        """
        raw = self.evaluate(expr, await_promise=True)
        return json.loads(raw) if raw else None

    # -- cookies -----------------------------------------------------------
    def get_cookies(self) -> list:
        return self._send("Network.getCookies").get("cookies", [])

    def set_cookie(self, name: str, value: str, domain: str, **kw) -> dict:
        return self._send("Network.setCookie", {"name": name, "value": value,
                                                   "domain": domain, **kw})

    # -- input ---------------------------------------------------------------
    def click(self, x: float, y: float) -> None:
        for event_type in ("mousePressed", "mouseReleased"):
            self._send("Input.dispatchMouseEvent", {
                "type": event_type, "x": x, "y": y, "button": "left", "clickCount": 1,
            })

    def close(self) -> None:
        try:
            self.ws.close()
        except Exception:
            pass


def _cli():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=9222)
    ap.add_argument("--navigate", help="URL to navigate to first")
    ap.add_argument("--eval", dest="expr", help="JS expression to evaluate and print")
    ap.add_argument("--cookies", action="store_true", help="print current cookies as JSON")
    args = ap.parse_args()

    c = CDP(host=args.host, port=args.port)
    try:
        if args.navigate:
            c.navigate(args.navigate)
            c.wait_load()
        if args.expr:
            print(json.dumps(c.evaluate(args.expr)))
        if args.cookies:
            print(json.dumps(c.get_cookies(), indent=2))
        if not (args.expr or args.cookies):
            print(f"Connected. document.title = {c.evaluate('document.title')!r}")
    finally:
        c.close()


if __name__ == "__main__":
    _cli()
