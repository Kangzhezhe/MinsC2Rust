import configparser
import os
import shutil
from dataclasses import dataclass


_CONFIG_INHERIT_SECTION = "Config"
_CONFIG_INHERIT_KEYS = ("inherits", "extends", "base_config")
_PATH_SECTION = "Paths"
_PATH_KEYS_TO_KEEP_LITERAL = {"output_project_name"}


@dataclass(frozen=True)
class ProjectPaths:
    """Stable project roots used by config setup.

    `setup_project_directories()` used to copy files via "../test_project",
    which only worked when the process cwd was `Tool/Tool_py`. Keeping the
    paths explicit makes uv/root-level execution behave the same way.
    """

    tool_root: str
    tool_py_root: str
    template_project_dir: str

    @classmethod
    def default(cls):
        tool_py_root = os.path.dirname(os.path.abspath(__file__))
        tool_root = os.path.dirname(tool_py_root)
        return cls(
            tool_root=tool_root,
            tool_py_root=tool_py_root,
            template_project_dir=os.path.join(tool_root, "test_project"),
        )


def _parse_param_value(raw_value: str):
    value = str(raw_value).strip()
    if not value:
        return value
    try:
        if any(ch in value for ch in (".", "e", "E")):
            parsed_float = float(value)
            if parsed_float.is_integer():
                return int(parsed_float)
            return parsed_float
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def _resolve_env_reference(raw_value: str) -> str:
    """Resolve `env:NAME` config values while keeping old literal values valid."""
    value = str(raw_value or "").strip().strip("'\"")
    if not value.startswith("env:"):
        return value
    env_name = value[len("env:") :].strip()
    if not env_name:
        return ""
    return os.getenv(env_name, "")


def _split_inherited_config_paths(raw_value: str):
    value = str(raw_value or "").strip()
    if not value:
        return []
    result = []
    for line in value.splitlines():
        for part in line.split(","):
            path = part.strip().strip("'\"")
            if path:
                result.append(path)
    return result


def _declared_inherited_configs(config_path: str):
    parser = configparser.ConfigParser()
    read_files = parser.read(config_path, encoding="utf-8")
    if not read_files:
        raise FileNotFoundError(f"config not found: {config_path}")
    if not parser.has_section(_CONFIG_INHERIT_SECTION):
        return []

    inherited = []
    for key in _CONFIG_INHERIT_KEYS:
        if not parser.has_option(_CONFIG_INHERIT_SECTION, key):
            continue
        inherited.extend(_split_inherited_config_paths(parser.get(_CONFIG_INHERIT_SECTION, key)))
    return inherited


def _resolve_config_path(reference: str, declaring_config_path: str):
    expanded = os.path.expanduser(os.path.expandvars(reference))
    if os.path.isabs(expanded):
        return os.path.abspath(expanded)
    return os.path.abspath(os.path.join(os.path.dirname(declaring_config_path), expanded))


def _collect_config_chain(config_path: str, visiting=None, collected=None):
    if visiting is None:
        visiting = []
    if collected is None:
        collected = []
    resolved_path = os.path.abspath(os.path.expanduser(os.path.expandvars(config_path)))
    real_path = os.path.realpath(resolved_path)

    if real_path in visiting:
        cycle = " -> ".join(visiting + [real_path])
        raise ValueError(f"config inheritance cycle detected: {cycle}")
    if real_path in collected:
        return collected

    parents = _declared_inherited_configs(resolved_path)
    visiting.append(real_path)
    for parent in parents:
        parent_path = _resolve_config_path(parent, resolved_path)
        _collect_config_chain(parent_path, visiting=visiting, collected=collected)
    visiting.pop()

    collected.append(real_path)
    return collected


def read_config(config_path):
    config = configparser.ConfigParser()
    config_chain = _collect_config_chain(config_path)
    for path in config_chain:
        current = configparser.ConfigParser()
        current.read(path, encoding="utf-8")
        if current.has_section(_PATH_SECTION):
            base_dir = os.path.dirname(os.path.abspath(path))
            for key, value in list(current.items(_PATH_SECTION)):
                if key in _PATH_KEYS_TO_KEEP_LITERAL:
                    continue
                raw_value = str(value or "").strip()
                if not raw_value:
                    continue
                expanded = os.path.expanduser(os.path.expandvars(raw_value))
                if os.path.isabs(expanded):
                    resolved = os.path.abspath(expanded)
                else:
                    resolved = os.path.abspath(os.path.join(base_dir, expanded))
                current.set(_PATH_SECTION, key, resolved)
        for section in current.sections():
            if section == _CONFIG_INHERIT_SECTION:
                continue
            if not config.has_section(section):
                config.add_section(section)
            for key, value in current.items(section):
                config.set(section, key, value)
    return config


def configure_llm_env(config):
    """Inject model API keys from config into process environment."""
    keys = (
        _resolve_env_reference(config.get("LLM_API_Keys", "qwen", fallback="")),
        _resolve_env_reference(config.get("LLM_API_Keys", "zhipu", fallback="")),
        _resolve_env_reference(config.get("LLM_API_Keys", "deepseek", fallback="")),
    )

    qwen_api_key, zhipu_api_key, deepseek_api_key = keys
    if qwen_api_key:
        os.environ["QWEN_API_KEY"] = qwen_api_key
    if zhipu_api_key:
        os.environ["ZHIPU_API_KEY"] = zhipu_api_key
    if deepseek_api_key:
        os.environ["DEEPSEEK_API_KEY"] = deepseek_api_key

    # OpenAI compatible settings
    openai_url = _resolve_env_reference(config.get("LLM_API_Keys", "openai_url", fallback=""))
    openai_api_key = _resolve_env_reference(config.get("LLM_API_Keys", "openai_api_key", fallback=""))
    openai_model = _resolve_env_reference(config.get("LLM_API_Keys", "openai_model", fallback=""))
    
    if openai_url:
        os.environ["OPENAI_API_BASE"] = openai_url.strip("'\"")
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key.strip("'\"")
    if openai_model:
        os.environ["OPENAI_MODEL_NAME"] = openai_model.strip("'\"")



def setup_project_directories(config, project_paths=None):
    configure_llm_env(config)
    project_paths = project_paths or ProjectPaths.default()

    tmp_dir = config['Paths']['tmp_dir']
    output_dir = config['Paths']['output_dir']
    output_project_name = config['Paths']['output_project_name']
    compile_commands_path = config['Paths']['compile_commands_path']


    os.makedirs(tmp_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    output_project_path = os.path.join(output_dir, output_project_name)
    os.makedirs(os.path.join(output_project_path, 'src'), exist_ok=True)
    os.makedirs(os.path.join(output_project_path, 'tests'), exist_ok=True)

    def copy_if_not_exists(src, dst):
        if not os.path.exists(dst):
            shutil.copy(src, dst)

    copy_if_not_exists(
        os.path.join(project_paths.template_project_dir, "Cargo.toml"),
        os.path.join(output_project_path, "Cargo.toml"),
    )
    copy_if_not_exists(
        os.path.join(project_paths.template_project_dir, "Cargo.lock"),
        os.path.join(output_project_path, "Cargo.lock"),
    )

    params = {key: _parse_param_value(config.get('Params', key)) for key in config['Params']}
    excluded_files = [file.strip() for file in config['ExcludeFiles']['files'].split(',')]


    enable_english_prompt = config.getboolean('Settings', 'enable_english_prompt')
    enable_multi_models = config.getboolean('Settings', 'enable_multi_models')
    model = config.get('Settings', 'model', fallback='qwen')
    params['enable_english_prompt'] = enable_english_prompt
    params['enable_multi_models'] = enable_multi_models
    params['model'] = model


    return tmp_dir, output_dir, output_project_path ,compile_commands_path ,params,excluded_files
