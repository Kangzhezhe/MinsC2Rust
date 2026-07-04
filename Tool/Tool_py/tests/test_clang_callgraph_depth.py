import sys
import unittest
from pathlib import Path


TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import clang_callgraph


class ClangCallgraphDepthTest(unittest.TestCase):
    def setUp(self):
        clang_callgraph.CALLGRAPH.clear()

    def tearDown(self):
        clang_callgraph.CALLGRAPH.clear()

    def test_get_func_depth_does_not_silently_truncate_deep_call_chain(self):
        for index in range(20):
            clang_callgraph.CALLGRAPH[f"f{index}()"] = [f"f{index + 1}()"]
        clang_callgraph.CALLGRAPH["f20()"] = []

        funcs_depth = {"f0()": 0}

        clang_callgraph.get_func_depth("f0()", [], funcs_depth=funcs_depth)

        self.assertIn("f20()", funcs_depth)
        self.assertEqual(funcs_depth["f20()"], 20)


if __name__ == "__main__":
    unittest.main()
