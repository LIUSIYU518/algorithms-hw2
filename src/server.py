import argparse
import json
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit

from src.shortener import URLShortener


HOME_PAGE = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>URL 단축기</title>
</head>
<body>
  <main>
    <h1>URL 단축기</h1>
    <form id="shorten-form">
      <label for="url">줄일 URL</label>
      <input id="url" name="url" type="url" required>
      <button type="submit">줄이기</button>
    </form>
    <p id="message" role="status"></p>
    <p><a href="/table">현재 해시 테이블 보기</a></p>
  </main>
  <script>
    const form = document.getElementById("shorten-form");
    const message = document.getElementById("message");
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      message.textContent = "";
      try {
        const response = await fetch("/shorten", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: form.elements.url.value })
        });
        const result = await response.json();
        if (!response.ok) {
          message.textContent = result.error || "URL을 줄이지 못했습니다.";
          return;
        }
        const link = document.createElement("a");
        link.href = result.short_url;
        link.textContent = result.short_url;
        message.replaceChildren(link);
      } catch (error) {
        message.textContent = error instanceof Error
          ? error.message
          : "요청을 처리하지 못했습니다.";
      }
    });
  </script>
</body>
</html>
"""


class ShortenerHTTPServer(HTTPServer):
    def __init__(self, server_address, shortener=None):
        self.shortener = shortener if shortener is not None else URLShortener()
        super().__init__(server_address, ShortenerRequestHandler)


class ShortenerRequestHandler(BaseHTTPRequestHandler):
    server: ShortenerHTTPServer

    def _send_bytes(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self._send_bytes(status, "application/json; charset=utf-8", body)

    def _send_not_found(self):
        self.send_error(404, "Not Found")

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            self._send_bytes(200, "text/html; charset=utf-8", HOME_PAGE.encode("utf-8"))
            return
        if path == "/table":
            body = self._table_page().encode("utf-8")
            self._send_bytes(200, "text/html; charset=utf-8", body)
            return
        if not path.startswith("/") or "/" in path[1:] or not path[1:]:
            self._send_not_found()
            return

        url = self.server.shortener.expand(path[1:])
        if url is None:
            self._send_not_found()
            return

        self.send_response(302)
        self.send_header("Location", url)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        if self.path != "/shorten":
            self._send_not_found()
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length < 0:
                raise ValueError("Content-Length must not be negative")
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            self._send_json(400, {"error": str(error)})
            return

        getter = getattr(payload, "get", None)
        if getter is None:
            self._send_json(400, {"error": "request body must be a JSON object"})
            return
        url = getter("url")

        existing_code = (
            self.server.shortener._url_to_code.get(url)
            if isinstance(url, str)
            else None
        )
        try:
            code = self.server.shortener.shorten(url)
        except (TypeError, ValueError) as error:
            self._send_json(400, {"error": str(error)})
            return

        host = self.headers.get(
            "Host", f"localhost:{self.server.server_port}"
        )
        short_url = f"http://{host}/{code}"
        status = 200 if existing_code is not None else 201
        self._send_json(status, {"code": code, "short_url": short_url})

    def _table_page(self):
        bucket_count = self.server.shortener._url_to_code.capacity
        host = self.headers.get("Host", f"localhost:{self.server.server_port}")
        rows = []

        for index, bucket in enumerate(self.server.shortener._url_to_code._buckets):
            nodes = []
            for url, code in bucket:
                safe_url = escape(url, quote=True)
                safe_code = escape(code, quote=True)
                calculations = []
                value = 0
                for position, character in enumerate(url, start=1):
                    previous = value
                    value = 31 * value + ord(character)
                    calculations.append(
                        "<li>h_{0} = (31 * {1}) + ord({2}) = {3}</li>".format(
                            position,
                            previous,
                            escape(repr(character)),
                            value,
                        )
                    )
                calculations.append(
                    "<li>bucket = {0} % {1} = {2}</li>".format(
                        value, bucket_count, index
                    )
                )
                short_link = escape(
                    f"http://{host}/{safe_code}", quote=True
                )
                nodes.append(
                    "<div class=\"node\">"
                    f"<strong>URL 키:</strong> <code>{safe_url}</code><br>"
                    f"<strong>짧은 코드:</strong> <code>{safe_code}</code><br>"
                    f"<strong>짧은 링크:</strong> "
                    f"<a href=\"{short_link}\">{short_link}</a>"
                    "<details><summary>호너 해시 계산 과정</summary>"
                    f"<ol>{''.join(calculations)}</ol></details>"
                    "</div>"
                )
            chain = " &rarr; ".join(nodes) if nodes else "<em>비어 있음</em>"
            rows.append(f"<tr><th scope=\"row\">{index}</th><td>{chain}</td></tr>")

        return (
            "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>현재 해시 테이블</title></head><body>"
            "<main><h1>현재 해시 테이블</h1><p><a href=\"/\">URL 줄이기</a></p>"
            "<table><thead><tr><th>버킷</th><th>연결 리스트 (노드 &rarr; 노드)</th>"
            "</tr></thead><tbody>"
            f"{''.join(rows)}</tbody></table></main></body></html>"
        )

    def do_PUT(self):
        self._send_not_found()

    def do_DELETE(self):
        self._send_not_found()

    def do_PATCH(self):
        self._send_not_found()

    def do_HEAD(self):
        self._send_not_found()

    def do_OPTIONS(self):
        self._send_not_found()

    def do_TRACE(self):
        self._send_not_found()

    def do_CONNECT(self):
        self._send_not_found()


def create_server(host="", port=8000):
    return ShortenerHTTPServer((host, port))


def main():
    parser = argparse.ArgumentParser(description="Run the URL shortener web server")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = create_server(port=args.port)
    print(f"Serving URL shortener on port {server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
