import sys
import tempfile
import unittest
from pathlib import Path


TOOL_PY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_PY_ROOT))

from cargo_verifier import CargoVerifier


class CargoVerifierTest(unittest.TestCase):
    def test_verify_project_does_not_depend_on_libc_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            verifier = CargoVerifier(base_tmp_dir=tmp)
            src_dir = Path(tmp) / "verify_project" / "src"
            src_dir.mkdir(parents=True)

            verifier._write_cargo_project(
                crate_name="verify_project",
                src_dir=str(src_dir),
                module_sources={"arraylist": "pub fn arraylist_new() -> i32 { 1 }"},
            )

            cargo_toml = (src_dir.parent / "Cargo.toml").read_text(encoding="utf-8")
            self.assertNotIn("libc =", cargo_toml)

    def test_verify_project_keeps_explicit_dependency_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            verifier = CargoVerifier(base_tmp_dir=tmp)
            verifier.dependency_overrides = {"regex": '"1"'}
            src_dir = Path(tmp) / "verify_project" / "src"
            src_dir.mkdir(parents=True)

            verifier._write_cargo_project(
                crate_name="verify_project",
                src_dir=str(src_dir),
                module_sources={"arraylist": "pub fn arraylist_new() -> i32 { 1 }"},
            )

            cargo_toml = (src_dir.parent / "Cargo.toml").read_text(encoding="utf-8")
            self.assertIn("[dependencies]", cargo_toml)
            self.assertIn('regex = "1"', cargo_toml)


if __name__ == "__main__":
    unittest.main()
