import configparser
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


TOOL_PY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_PY_ROOT))

from parse_config import ProjectPaths, _resolve_env_reference, configure_llm_env, read_config, setup_project_directories


class ParseConfigTest(unittest.TestCase):
    def test_read_config_inherits_parent_and_child_overrides_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "base.ini"
            child = root / "child.ini"
            base.write_text(
                """
[Paths]
src_dir = base-src
tmp_dir = base-tmp

[LLM_API_Keys]
openai_api_key = base-key

[Params]
max_retries = 10
test_runtime_check_mode = source_complete
cc_mini_max_call_attempts = 3
""".lstrip(),
                encoding="utf-8",
            )
            child.write_text(
                """
[Config]
inherits = base.ini

[Paths]
src_dir = child-src

[Params]
max_retries = 2
""".lstrip(),
                encoding="utf-8",
            )

            cfg = read_config(str(child))

            self.assertEqual(cfg["Paths"]["src_dir"], str(child.parent / "child-src"))
            self.assertEqual(cfg["Paths"]["tmp_dir"], str(base.parent / "base-tmp"))
            self.assertEqual(cfg["LLM_API_Keys"]["openai_api_key"], "base-key")
            self.assertEqual(cfg["Params"]["max_retries"], "2")
            self.assertEqual(cfg["Params"]["test_runtime_check_mode"], "source_complete")
            self.assertEqual(cfg["Params"]["cc_mini_max_call_attempts"], "3")

    def test_read_config_resolves_paths_relative_to_the_declaring_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_root = root / "configs"
            exp_root = config_root / "exp"
            config_root.mkdir()
            exp_root.mkdir()
            base = config_root / "config.example.ini"
            child = exp_root / "case.ini"
            base.write_text(
                """
[Paths]
func_result_dir = ../Tool/func_result
tmp_dir = ../Output/example/tmp
output_dir = ../Output/example/Output
compile_commands_path = ../benchmarks/example/build/compile_commands.json

[Params]
max_retries = 5
""".lstrip(),
                encoding="utf-8",
            )
            child.write_text(
                """
[Config]
inherits = ../config.example.ini

[Paths]
src_dir = ../../benchmarks/case/src
tmp_dir = ../../benchmarks/case/Output/tmp
""".lstrip(),
                encoding="utf-8",
            )

            cfg = read_config(str(child))

            self.assertEqual(cfg["Paths"]["func_result_dir"], str((config_root / "../Tool/func_result").resolve()))
            self.assertEqual(
                cfg["Paths"]["compile_commands_path"],
                str((config_root / "../benchmarks/example/build/compile_commands.json").resolve()),
            )
            self.assertEqual(cfg["Paths"]["src_dir"], str((exp_root / "../../benchmarks/case/src").resolve()))
            self.assertEqual(cfg["Paths"]["tmp_dir"], str((exp_root / "../../benchmarks/case/Output/tmp").resolve()))

    def test_read_config_resolves_inherited_paths_relative_to_declaring_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parent_dir = root / "parents"
            child_dir = root / "children"
            parent_dir.mkdir()
            child_dir.mkdir()
            base = parent_dir / "base.ini"
            child = child_dir / "child.ini"
            base.write_text("[Params]\nmax_retries = 10\n", encoding="utf-8")
            child.write_text("[Config]\ninherits = ../parents/base.ini\n", encoding="utf-8")

            cfg = read_config(str(child))

            self.assertEqual(cfg["Params"]["max_retries"], "10")

    def test_read_config_rejects_inheritance_cycles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "first.ini"
            second = root / "second.ini"
            first.write_text("[Config]\ninherits = second.ini\n", encoding="utf-8")
            second.write_text("[Config]\ninherits = first.ini\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                read_config(str(first))

    def test_all_shipped_runtime_configs_are_readable_and_inherit_base_config(self):
        config_root = TOOL_PY_ROOT.parents[1] / "configs"
        base_configs = {
            config_root / "config.ini",
            config_root / "config.example.ini",
        }

        if not config_root.exists():
            self.skipTest(f"config directory not found: {config_root}")

        for path in sorted(config_root.rglob("*.ini")):
            with self.subTest(config=str(path.relative_to(config_root))):
                cfg = read_config(str(path))
                self.assertIn("Paths", cfg)
                self.assertIn("Params", cfg)
                self.assertIn("Settings", cfg)
                self.assertIn("LLM_API_Keys", cfg)
                self.assertIn("ExcludeFiles", cfg)
                self.assertIn("tmp_dir", cfg["Paths"])
                self.assertIn("output_dir", cfg["Paths"])
                self.assertIn("compile_commands_path", cfg["Paths"])
                if path not in base_configs:
                    raw = configparser.ConfigParser()
                    raw.read(path, encoding="utf-8")
                    self.assertTrue(raw.has_section("Config"))
                    self.assertTrue(raw.has_option("Config", "inherits"))

    def test_resolve_env_reference_keeps_literals_and_reads_environment(self):
        with patch.dict(os.environ, {"MODEL_KEY": "secret-value"}, clear=False):
            self.assertEqual(_resolve_env_reference("literal"), "literal")
            self.assertEqual(_resolve_env_reference("'quoted'"), "quoted")
            self.assertEqual(_resolve_env_reference("env:MODEL_KEY"), "secret-value")
            self.assertEqual(_resolve_env_reference("env:MISSING_MODEL_KEY"), "")

    def test_configure_llm_env_supports_env_references(self):
        cfg = configparser.ConfigParser()
        cfg["LLM_API_Keys"] = {
            "qwen": "env:QWEN_TEST_KEY",
            "zhipu": "",
            "deepseek": "literal-deepseek",
            "openai_url": "'https://example.test/v1'",
            "openai_api_key": "env:OPENAI_TEST_KEY",
            "openai_model": "gpt-test",
        }

        with patch.dict(
            os.environ,
            {
                "QWEN_TEST_KEY": "qwen-secret",
                "OPENAI_TEST_KEY": "openai-secret",
            },
            clear=False,
        ):
            configure_llm_env(cfg)

            self.assertEqual(os.environ["QWEN_API_KEY"], "qwen-secret")
            self.assertEqual(os.environ["DEEPSEEK_API_KEY"], "literal-deepseek")
            self.assertEqual(os.environ["OPENAI_API_BASE"], "https://example.test/v1")
            self.assertEqual(os.environ["OPENAI_API_KEY"], "openai-secret")
            self.assertEqual(os.environ["OPENAI_MODEL_NAME"], "gpt-test")

    def test_setup_project_directories_uses_explicit_template_paths(self):
        cfg = configparser.ConfigParser()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template_dir = root / "template_project"
            template_dir.mkdir()
            (template_dir / "Cargo.toml").write_text("[package]\nname = \"template\"\n", encoding="utf-8")
            (template_dir / "Cargo.lock").write_text("# lock\n", encoding="utf-8")

            cfg["LLM_API_Keys"] = {}
            cfg["Paths"] = {
                "tmp_dir": str(root / "tmp"),
                "output_dir": str(root / "out"),
                "output_project_name": "verify_project",
                "compile_commands_path": str(root / "compile_commands.json"),
            }
            cfg["Params"] = {"max_retries": "2", "temperature": "0.1"}
            cfg["ExcludeFiles"] = {"files": ""}
            cfg["Settings"] = {
                "enable_english_prompt": "false",
                "enable_multi_models": "true",
                "model": "openai",
            }
            project_paths = ProjectPaths(
                tool_root=str(root),
                tool_py_root=str(root / "Tool_py"),
                template_project_dir=str(template_dir),
            )

            previous_cwd = os.getcwd()
            try:
                os.chdir("/")
                tmp_dir, output_dir, output_project_path, compile_commands_path, params, excluded = (
                    setup_project_directories(cfg, project_paths=project_paths)
                )
            finally:
                os.chdir(previous_cwd)

            self.assertEqual(tmp_dir, str(root / "tmp"))
            self.assertEqual(output_dir, str(root / "out"))
            self.assertEqual(compile_commands_path, str(root / "compile_commands.json"))
            self.assertEqual(params["max_retries"], 2)
            self.assertEqual(params["temperature"], 0.1)
            self.assertTrue(params["enable_multi_models"])
            self.assertEqual(params["model"], "openai")
            self.assertEqual(excluded, [""])
            self.assertTrue((Path(output_project_path) / "Cargo.toml").is_file())
            self.assertTrue((Path(output_project_path) / "Cargo.lock").is_file())


if __name__ == "__main__":
    unittest.main()
