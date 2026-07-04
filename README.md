# MinsC2Rust

MinsC2Rust is an LLM-assisted C-to-Rust transpilation pipeline. It decomposes a C project into function-level units, translates functions with dependency context, verifies generated Rust with Cargo, and reconstructs a testable Rust project.

This repository is being prepared as the public core release. The first public scope is intentionally small:

- core transpilation tool: `Tool/`
- CC-MINI runtime repair agent: `cc_mini/`
- repository entry scripts: `scripts/`
- public benchmarks: `benchmarks/arraylist/`, `benchmarks/c-algorithm/`, and `benchmarks/crown/Input/`
- root-level runtime configs: `configs/`

`ds-free-api/` is a private service and is not required by this public release. Any OpenAI-compatible endpoint can be used.

Chinese documentation is available in [README_zh.md](README_zh.md).

## Repository Layout

```text
.
├── Tool/                  # Main transpilation pipeline
├── cc_mini/               # Optional agent fallback for runtime/test repair
├── configs/               # Runtime configuration files
├── benchmarks/            # Public C input benchmarks
│   ├── arraylist/         # Default smoke benchmark
│   ├── c-algorithm/       # Larger algorithm/data-structure benchmark
│   └── crown/Input/       # Curated Crown input subset
├── scripts/               # Convenience entrypoints
├── .cc-mini.example.toml  # CC-MINI config template
└── README.md
```

Generated files are written to `Output/` and are ignored by Git.

## Requirements

Tested environment:

- Python 3.12
- Rust stable
- Cargo
- Clang / libclang
- CMake and basic C build tools
- An OpenAI-compatible LLM endpoint

Ubuntu/Debian example:

```bash
sudo apt-get update
sudo apt-get install -y git build-essential cmake clang libclang-dev graphviz universal-ctags

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
rustup default stable
rustup component add rustfmt
```

Python environment:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

cd MinsC2Rust
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r Tool/requirements.txt
```

## Configuration

MinsC2Rust uses two independent LLM configurations.

### 1. Main Transpilation Config

The main pipeline reads INI files from the root-level `configs/` directory.

Create a local private config:

```bash
cp configs/config.example.ini configs/config.ini
```

Edit `configs/config.ini` and set your main translation model:

```ini
[LLM_API_Keys]
openai_url = https://your-openai-compatible-endpoint/v1
openai_api_key = YOUR_TOOL_API_KEY
openai_model = your-model-name
```

`configs/config.ini` is ignored by Git. Do not commit real API keys.

The default public config is `configs/config.example.ini`, which targets the `arraylist` smoke benchmark. Two larger public benchmark configs are also included:

```text
configs/config_c_algorithm.ini
configs/config_crown.ini
```

These child configs inherit common settings from `configs/config.example.ini` and only override the benchmark paths and exclusions.

### 2. CC-MINI Agent Config

CC-MINI is used by runtime repair and fallback flows. It has a separate config file and may use a different provider, API key, base URL, and model.

Create a local private config:

```bash
cp .cc-mini.example.toml .cc-mini.toml
```

Edit `.cc-mini.toml`:

```toml
provider = "openai"
stream = false

[openai]
api_key = "YOUR_CC_MINI_API_KEY"
base_url = "https://your-openai-compatible-endpoint/v1"
model = "your-model-name"
use_finish_tool = true

[fallback]
enabled = false
provider = "openai"
api_key = "YOUR_FALLBACK_API_KEY"
base_url = "https://your-fallback-endpoint/v1"
model = "your-fallback-model-name"
```

`.cc-mini.toml` is ignored by Git.

## Running the Arraylist Smoke Test

The smoke test uses `benchmarks/arraylist/` and writes to `Output/arraylist_smoke_current/`.

```bash
./scripts/smoke_test.sh
```

## Running Other Public Benchmarks

After creating `configs/config.ini` and `.cc-mini.toml`, you can run the larger public benchmark configs directly:

```bash
cd Tool
./run.sh ../configs/config_c_algorithm.ini
./run.sh ../configs/config_crown.ini
```

These runs are larger than the default smoke test and may require more model calls and runtime repair iterations.

Important outputs:

```text
Output/arraylist_smoke_current/
├── Output/
│   ├── results.json
│   ├── all_error_funcs_content.json
│   ├── report.md
│   ├── logs/
│   └── state/
└── tmp/
```

`report.md` is the first file to inspect after a run. It summarizes compile/test status, retry behavior, runtime repair, and major failure categories.

## Running the Tool Directly

From the repository root:

```bash
cd Tool
./run.sh ../configs/config.ini
```

The default `Tool/run.sh` config is also `../configs/config.ini`, so this is equivalent after local config setup:

```bash
cd Tool
./run.sh
```

## Notes on Correctness

The current pipeline validates generated Rust with Cargo compilation, runtime tests, round-trip checks, and optional CC-MINI repair. This is practical validation, not a formal proof of semantic equivalence.

Generated Rust is usually safe and test-oriented, but it may remain C-shaped rather than fully idiomatic Rust. Idiomatic Rustification is a separate optimization layer.

## Secret Handling

Before publishing a fork or public snapshot:

```bash
rg -n --hidden "sk-|api_key|password|Bearer|token" .
```

Rotate any API key that was ever committed to Git history. If you publish an existing repository history, clean it with a history rewriting tool such as `git-filter-repo`. A safer option is to publish a new clean repository snapshot.

## License

See [LICENSE](LICENSE).
