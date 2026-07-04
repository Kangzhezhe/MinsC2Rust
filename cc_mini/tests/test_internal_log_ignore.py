import tempfile
import unittest
from pathlib import Path

from cc_mini.tools.file_read import FileReadTool
from cc_mini.tools.file_edit import FileEditTool
from cc_mini.tools.file_write import FileWriteTool
from cc_mini.tools.glob_tool import GlobTool
from cc_mini.tools.grep_tool import GrepTool


class InternalLogIgnoreTest(unittest.TestCase):
    def test_read_refuses_internal_llm_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_path = root / "cc-mini-llm.log"
            log_path.write_text("secret prompt payload", encoding="utf-8")

            result = FileReadTool().execute(str(log_path))

            self.assertTrue(result.is_error)
            self.assertIn("Refusing to read internal CC-MINI log file", result.content)
            self.assertNotIn("secret prompt payload", result.content)

    def test_read_allows_regular_project_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "src" / "lib.rs"
            source_path.parent.mkdir()
            source_path.write_text("pub fn ok() {}\n", encoding="utf-8")

            result = FileReadTool().execute(str(source_path))

            self.assertFalse(result.is_error)
            self.assertIn("pub fn ok()", result.content)

    def test_read_refuses_target_directory_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact_path = root / "target" / "debug" / "build.log"
            artifact_path.parent.mkdir(parents=True)
            artifact_path.write_text("artifact payload", encoding="utf-8")

            result = FileReadTool().execute(str(artifact_path))

            self.assertTrue(result.is_error)
            self.assertIn("Ignored target directory path", result.content)
            self.assertNotIn("artifact payload", result.content)

    def test_read_does_not_block_target_substring_file_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "src" / "target_utils.rs"
            source_path.parent.mkdir()
            source_path.write_text("pub fn target_utils() {}\n", encoding="utf-8")

            result = FileReadTool().execute(str(source_path))

            self.assertFalse(result.is_error)
            self.assertIn("target_utils", result.content)

    def test_glob_omits_internal_llm_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "cc-mini-llm.log").write_text("request", encoding="utf-8")
            (root / "cc-mini-llm-raw.txt").write_text("raw request", encoding="utf-8")
            (root / "src.rs").write_text("pub fn ok() {}\n", encoding="utf-8")

            result = GlobTool().execute("**/*", path=str(root))

            self.assertFalse(result.is_error)
            self.assertIn("src.rs", result.content)
            self.assertNotIn("cc-mini-llm.log", result.content)
            self.assertNotIn("cc-mini-llm-raw.txt", result.content)

    def test_glob_omits_target_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "target" / "debug").mkdir(parents=True)
            (root / "target" / "debug" / "build.log").write_text("artifact", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "target_utils.rs").write_text("source", encoding="utf-8")

            result = GlobTool().execute("**/*", path=str(root))

            self.assertFalse(result.is_error)
            self.assertIn("src/target_utils.rs", result.content)
            self.assertNotIn("target/debug", result.content)
            self.assertNotIn("build.log", result.content)

    def test_glob_from_target_root_returns_no_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_root = root / "target"
            target_root.mkdir()
            (target_root / "debug.log").write_text("artifact", encoding="utf-8")

            result = GlobTool().execute("**/*", path=str(target_root))

            self.assertFalse(result.is_error)
            self.assertEqual(result.content, "No files found matching the pattern.")

    def test_grep_omits_internal_llm_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "cc-mini-llm.log").write_text("needle in log", encoding="utf-8")
            (root / "cc-mini-llm-raw.txt").write_text("needle in raw", encoding="utf-8")
            (root / "src.rs").write_text("needle in source\n", encoding="utf-8")

            result = GrepTool().execute("needle", path=str(root), output_mode="content")

            self.assertFalse(result.is_error)
            self.assertIn("src.rs", result.content)
            self.assertIn("needle in source", result.content)
            self.assertNotIn("cc-mini-llm.log", result.content)
            self.assertNotIn("cc-mini-llm-raw.txt", result.content)
            self.assertNotIn("needle in log", result.content)
            self.assertNotIn("needle in raw", result.content)

    def test_grep_omits_target_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "target" / "debug").mkdir(parents=True)
            (root / "target" / "debug" / "build.log").write_text("needle in artifact", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "lib.rs").write_text("needle in source\n", encoding="utf-8")

            result = GrepTool().execute("needle", path=str(root), output_mode="content")

            self.assertFalse(result.is_error)
            self.assertIn("src", result.content)
            self.assertIn("needle in source", result.content)
            self.assertNotIn("target", result.content)
            self.assertNotIn("needle in artifact", result.content)

    def test_grep_refuses_target_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_root = root / "target"
            target_root.mkdir()
            (target_root / "debug.log").write_text("needle", encoding="utf-8")

            result = GrepTool().execute("needle", path=str(target_root), output_mode="content")

            self.assertTrue(result.is_error)
            self.assertIn("Ignored target directory path", result.content)

    def test_write_refuses_target_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact_path = root / "target" / "debug" / "new.log"

            result = FileWriteTool().execute(str(artifact_path), "artifact")

            self.assertTrue(result.is_error)
            self.assertIn("Ignored target directory path", result.content)
            self.assertFalse(artifact_path.exists())

    def test_edit_refuses_target_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact_path = root / "target" / "debug" / "build.log"
            artifact_path.parent.mkdir(parents=True)
            artifact_path.write_text("old artifact", encoding="utf-8")

            result = FileEditTool().execute(str(artifact_path), "old", "new")

            self.assertTrue(result.is_error)
            self.assertIn("Ignored target directory path", result.content)
            self.assertEqual(artifact_path.read_text(encoding="utf-8"), "old artifact")


if __name__ == "__main__":
    unittest.main()
