import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_encode_uses_requested_digit_order(self):
        expected = {
            0: "0",
            9: "9",
            10: "a",
            35: "z",
            36: "A",
            61: "Z",
            62: "10",
        }
        for number, encoded in expected.items():
            with self.subTest(number=number):
                self.assertEqual(encode(number), encoded)

    def test_decode_uses_requested_digit_order(self):
        expected = {
            "0": 0,
            "9": 9,
            "a": 10,
            "z": 35,
            "A": 36,
            "Z": 61,
            "10": 62,
        }
        for encoded, number in expected.items():
            with self.subTest(encoded=encoded):
                self.assertEqual(decode(encoded), number)

    def test_encode_and_decode_round_trip(self):
        numbers = [0, 1, 61, 62, 63, 3843, 3844, 2**128]
        for number in numbers:
            with self.subTest(number=number):
                self.assertEqual(decode(encode(number)), number)

    def test_encode_rejects_negative_and_non_integer_values(self):
        with self.assertRaises(ValueError):
            encode(-1)
        with self.assertRaises(TypeError):
            encode(1.5)

    def test_encode_rejects_bool(self):
        with self.assertRaises((TypeError, ValueError)):
            encode(True)

    def test_decode_rejects_non_string_values(self):
        for value in (None, 123, True):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    decode(value)

    def test_decode_rejects_empty_or_invalid_strings(self):
        with self.assertRaises(ValueError):
            decode("")
        with self.assertRaises(ValueError):
            decode("a!")


if __name__ == "__main__":
    unittest.main()
