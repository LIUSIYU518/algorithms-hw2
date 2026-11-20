import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_empty_table_returns_none_for_missing_key(self):
        table = HashTable()

        self.assertIsNone(table.get("missing"))
        self.assertEqual(len(table), 0)
        self.assertEqual(table.capacity, 8)

    def test_setting_existing_key_updates_value_without_increasing_size(self):
        table = HashTable()

        table.set("key", "first")
        table.set("key", "updated")

        self.assertEqual(table.get("key"), "updated")
        self.assertEqual(len(table), 1)

    def test_colliding_keys_can_be_stored_retrieved_and_updated(self):
        table = HashTable()
        # "a", "i", and "q" all map to bucket 1 with eight buckets.
        for key in ("a", "i", "q"):
            table.set(key, f"value-{key}")

        self.assertEqual(table.get("a"), "value-a")
        self.assertEqual(table.get("i"), "value-i")
        self.assertEqual(table.get("q"), "value-q")

        table.set("i", "updated")
        self.assertEqual(table.get("a"), "value-a")
        self.assertEqual(table.get("i"), "updated")
        self.assertEqual(table.get("q"), "value-q")
        self.assertEqual(len(table), 3)

    def test_table_resizes_only_after_load_factor_exceeds_three_quarters(self):
        table = HashTable()
        for index in range(6):
            table.set(f"key-{index}", index)

        self.assertEqual(table.capacity, 8)
        self.assertEqual(len(table), 6)

        table.set("key-6", 6)

        self.assertEqual(table.capacity, 16)
        self.assertEqual(len(table), 7)
        for index in range(7):
            with self.subTest(index=index):
                self.assertEqual(table.get(f"key-{index}"), index)


if __name__ == "__main__":
    unittest.main()
