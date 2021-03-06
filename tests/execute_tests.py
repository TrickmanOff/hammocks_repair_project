import os
import sys
import unittest

if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)

    from tests.test_hammocks_covering import MinimalHammockTest, HammocksCoveringTest
    test_minimal_hammock = MinimalHammockTest()
    test_hammocks_covering = HammocksCoveringTest()

    from tests.test_bad_pairs_selection import BadPairsSelectionTest
    test_bad_pairs_selection = BadPairsSelectionTest()

    from tests.test_repair import HammocksReplacementRepairTest
    test_hammocks_replacement_repair = HammocksReplacementRepairTest()

    unittest.main()
