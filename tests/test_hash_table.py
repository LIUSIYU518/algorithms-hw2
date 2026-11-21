import unittest

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


class HashTableTests(unittest.TestCase):
    table_classes = (HashTable, LinearProbingHashTable)

    def test_empty_table_returns_none_for_missing_key(self):
        for table_class in self.table_classes:
            with self.subTest(table_class=table_class.__name__):
                table = table_class()

                self.assertIsNone(table.get("missing"))
                self.assertEqual(len(table), 0)
                self.assertEqual(table.capacity, 8)

    def test_setting_existing_key_updates_value_without_increasing_size(self):
        for table_class in self.table_classes:
            with self.subTest(table_class=table_class.__name__):
                table = table_class()

                table.set("key", "first")
                table.set("key", "updated")

                self.assertEqual(table.get("key"), "updated")
                self.assertEqual(len(table), 1)

    def test_colliding_keys_can_be_stored_retrieved_and_updated(self):
        for table_class in self.table_classes:
            with self.subTest(table_class=table_class.__name__):
                table = table_class(max_load=None)
                # "a", "i", and "q" all have home index 1 with eight slots.
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
        for table_class in self.table_classes:
            with self.subTest(table_class=table_class.__name__):
                table = table_class()
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

    def test_none_max_load_keeps_capacity_fixed(self):
        for table_class in self.table_classes:
            with self.subTest(table_class=table_class.__name__):
                table = table_class(capacity=8, max_load=None)

                for index in range(6):
                    table.set(f"key-{index}", index)

                self.assertEqual(table.capacity, 8)
                self.assertEqual(len(table), 6)

    def test_get_with_comparisons_counts_nodes_or_checked_cells(self):
        for table_class in self.table_classes:
            with self.subTest(table_class=table_class.__name__):
                table = table_class(max_load=None)
                for key in ("a", "i", "q"):
                    table.set(key, f"value-{key}")

                self.assertEqual(table.get_with_comparisons("a"), ("value-a", 1))
                self.assertEqual(table.get_with_comparisons("i"), ("value-i", 2))
                self.assertEqual(table.get_with_comparisons("q"), ("value-q", 3))
                if table_class is HashTable:
                    self.assertEqual(table.get_with_comparisons("y"), (None, 3))
                    self.assertEqual(
                        table.get_with_comparisons("missing"), (None, 0)
                    )
                else:
                    self.assertEqual(table.get_with_comparisons("y"), (None, 4))
                    self.assertEqual(
                        table.get_with_comparisons("missing"), (None, 1)
                    )

    def test_linear_probing_wraps_from_last_slot_to_zero(self):
        table = LinearProbingHashTable(max_load=None)
        for key in ("g", "o", "w"):
            table.set(key, f"value-{key}")

        self.assertEqual(
            [entry[0] if entry is not None else None for entry in table._slots],
            ["o", "w", None, None, None, None, None, "g"],
        )
        self.assertEqual(table.get_with_comparisons("w"), ("value-w", 3))
        self.assertEqual(table.get_with_comparisons("_"), (None, 4))

    def test_full_linear_table_can_be_read_and_rejects_an_extra_key(self):
        table = LinearProbingHashTable(capacity=4, max_load=None)
        for index in range(4):
            table.set(f"key-{index}", index)

        self.assertEqual(len(table), 4)
        for index in range(4):
            with self.subTest(index=index):
                self.assertEqual(table.get(f"key-{index}"), index)
        self.assertEqual(table.get_with_comparisons("missing"), (None, 4))
        with self.assertRaises(OverflowError):
            table.set("another-key", 4)


if __name__ == "__main__":
    unittest.main()
