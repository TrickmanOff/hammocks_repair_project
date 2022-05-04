import os
import sys
import unittest


if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)

    from tests.test_minimal_hammock import MinimalHammockTest
    test_minimal_hammock = MinimalHammockTest()

    unittest.main()
