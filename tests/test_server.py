import json
import threading
import unittest
from http.client import HTTPConnection

from src.server import create_server


class URLShortenerServerTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server("127.0.0.1", 0)
        thread = threading.Thread(target=self.server.serve_forever)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = response.status, response.getheaders(), response.read()
        connection.close()
        return result

    def test_home_page_has_url_form_and_table_link(self):
        status, headers, body = self.request("GET", "/")

        self.assertEqual(status, 200)
        self.assertIn("text/html", dict(headers)["Content-Type"])
        self.assertIn(b'id="url"', body)
        self.assertIn("줄이기".encode("utf-8"), body)
        self.assertIn(b'href="/table"', body)

    def test_shorten_returns_created_then_ok_and_redirects(self):
        url = "https://example.com/a?x=1"
        request_body = json.dumps({"url": url})
        headers = {"Content-Type": "application/json"}

        status, _, body = self.request("POST", "/shorten", request_body, headers)
        first_result = json.loads(body)
        self.assertEqual(status, 201)
        self.assertEqual(
            first_result["short_url"],
            f"http://127.0.0.1:{self.server.server_port}/{first_result['code']}",
        )

        status, _, body = self.request("POST", "/shorten", request_body, headers)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), first_result)

        status, response_headers, _ = self.request(
            "GET", f"/{first_result['code']}"
        )
        self.assertEqual(status, 302)
        self.assertEqual(dict(response_headers)["Location"], url)

    def test_bad_json_and_invalid_url_return_json_400(self):
        status, headers, body = self.request(
            "POST",
            "/shorten",
            "{",
            {"Content-Type": "application/json"},
        )
        self.assertEqual(status, 400)
        self.assertIn("application/json", dict(headers)["Content-Type"])
        self.assertIn("error", json.loads(body))

        status, _, body = self.request(
            "POST",
            "/shorten",
            json.dumps({"url": "/relative"}),
            {"Content-Type": "application/json"},
        )
        self.assertEqual(status, 400)
        self.assertIn("error", json.loads(body))

        status, _, body = self.request(
            "POST",
            "/shorten",
            json.dumps([]),
            {"Content-Type": "application/json"},
        )
        self.assertEqual(status, 400)
        self.assertIn("error", json.loads(body))

    def test_table_shows_chained_nodes_and_horner_calculations(self):
        self.request(
            "POST",
            "/shorten",
            json.dumps({"url": "https://example.com/one"}),
            {"Content-Type": "application/json"},
        )
        self.request(
            "POST",
            "/shorten",
            json.dumps({"url": "https://example.com/three"}),
            {"Content-Type": "application/json"},
        )

        status, headers, body = self.request("GET", "/table")
        page = body.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn("text/html", dict(headers)["Content-Type"])
        self.assertIn("https://example.com/one", page)
        self.assertIn("https://example.com/three", page)
        self.assertIn("&rarr;", page)
        self.assertIn("<details>", page)
        self.assertIn("31 *", page)
        self.assertIn("bucket =", page)
        self.assertIn("href=\"http://127.0.0.1:", page)

    def test_unknown_routes_and_codes_return_404(self):
        status, _, _ = self.request("GET", "/missing")
        self.assertEqual(status, 404)

        status, _, _ = self.request("GET", "/one/two")
        self.assertEqual(status, 404)

        status, _, _ = self.request("POST", "/other")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
