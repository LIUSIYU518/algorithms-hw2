import unittest

from src.shortener import URLShortener


class URLShortenerTests(unittest.TestCase):
    strategies = ("chaining", "linear_probing")

    def test_http_and_https_urls_are_shortened_and_expanded_unchanged(self):
        urls = [
            "http://example.com/path?query=value#fragment",
            "https://example.org/",
        ]

        for strategy in self.strategies:
            shortener = URLShortener(strategy=strategy)
            for url in urls:
                with self.subTest(strategy=strategy, url=url):
                    code = shortener.shorten(url)
                    self.assertIsInstance(code, str)
                    self.assertTrue(code)
                    self.assertEqual(shortener.expand(code), url)

    def test_repeated_url_returns_the_existing_code(self):
        url = "https://example.com/repeated"

        for strategy in self.strategies:
            with self.subTest(strategy=strategy):
                shortener = URLShortener(strategy=strategy)
                first_code = shortener.shorten(url)
                second_code = shortener.shorten(url)

                self.assertEqual(second_code, first_code)

    def test_distinct_urls_receive_distinct_codes(self):
        for strategy in self.strategies:
            with self.subTest(strategy=strategy):
                shortener = URLShortener(strategy=strategy)

                first_code = shortener.shorten("https://example.com/one")
                second_code = shortener.shorten("https://example.com/two")

                self.assertNotEqual(first_code, second_code)

    def test_missing_or_invalid_codes_expand_to_none(self):
        for strategy in self.strategies:
            with self.subTest(strategy=strategy):
                shortener = URLShortener(strategy=strategy)

                self.assertIsNone(shortener.expand("999"))
                self.assertIsNone(shortener.expand("not-valid!"))

    def test_new_instance_does_not_retain_previous_mappings(self):
        for strategy in self.strategies:
            with self.subTest(strategy=strategy):
                first_shortener = URLShortener(strategy=strategy)
                code = first_shortener.shorten("https://example.com/temporary")

                restarted_shortener = URLShortener(strategy=strategy)

                self.assertIsNone(restarted_shortener.expand(code))

    def test_rejects_urls_with_whitespace_relative_urls_unsupported_schemes_or_no_host(self):
        invalid_urls = [
            " https://example.com/path",
            "https://example.com/path ",
            "https://example.com/a b",
            "/relative/path",
            "ftp://example.com/file",
            "mailto:user@example.com",
            "http:///missing-host",
            "not a URL",
        ]

        for strategy in self.strategies:
            shortener = URLShortener(strategy=strategy)
            for url in invalid_urls:
                with self.subTest(strategy=strategy, url=url):
                    with self.assertRaises(ValueError):
                        shortener.shorten(url)

    def test_rejects_unknown_hash_table_strategy(self):
        with self.assertRaises(ValueError):
            URLShortener(strategy="unknown")


if __name__ == "__main__":
    unittest.main()
