# MinsC2Rust

MinsC2Rust 是一个 LLM 辅助的 C 到 Rust 转译流程。它会把 C 项目拆成函数级单元，结合依赖上下文逐步转译，用 Cargo 验证生成的 Rust，并重建可测试的 Rust 项目。

当前仓库正在整理为公开核心版本。第一版公开范围刻意收窄：

- 核心转译工具：`Tool/`
- CC-MINI runtime repair agent：`cc_mini/`
- 仓库入口脚本：`scripts/`
- 公开 benchmark：`benchmarks/arraylist/`、`benchmarks/c-algorithm/`、`benchmarks/crown/Input/`
- 根目录配置：`configs/`

`ds-free-api/` 是私有服务，不作为公开版本的必需组件。公开版本只要求可用的 OpenAI-compatible endpoint。

英文文档见 [README.md](README.md)。

## 目录结构

```text
.
├── Tool/                  # 主转译流程
├── cc_mini/               # 可选的 agent fallback/runtime repair
├── configs/               # 运行配置
├── benchmarks/            # 公开 C 输入 benchmark
│   ├── arraylist/         # 默认 smoke benchmark
│   ├── c-algorithm/       # 较大的算法/数据结构 benchmark
│   └── crown/Input/       # 精简后的 Crown 输入子集
├── scripts/               # 入口脚本
├── .cc-mini.example.toml  # CC-MINI 配置模板
└── README.md
```

运行输出写入 `Output/`，该目录默认不提交 Git。

## 依赖

建议环境：

- Python 3.12
- Rust stable
- Cargo
- Clang / libclang
- CMake 和基础 C 构建工具
- 一个 OpenAI-compatible LLM endpoint

Ubuntu/Debian 示例：

```bash
sudo apt-get update
sudo apt-get install -y git build-essential cmake clang libclang-dev graphviz universal-ctags

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
rustup default stable
rustup component add rustfmt
```

Python 环境：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

cd MinsC2Rust
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r Tool/requirements.txt
```

## 配置

系统有两套独立 LLM 配置。

### 1. 主转译流程配置

主流程读取根目录 `configs/` 下的 INI 配置。

创建本地私有配置：

```bash
cp configs/config.example.ini configs/config.ini
```

编辑 `configs/config.ini`：

```ini
[LLM_API_Keys]
openai_url = https://your-openai-compatible-endpoint/v1
openai_api_key = YOUR_TOOL_API_KEY
openai_model = your-model-name
```

`configs/config.ini` 已加入 `.gitignore`，不要提交真实 API key。

默认公开配置是 `configs/config.example.ini`，它指向 `arraylist` smoke benchmark。仓库还包含两个较大的公开 benchmark 配置：

```text
configs/config_c_algorithm.ini
configs/config_crown.ini
```

这两个子配置继承 `configs/config.example.ini` 中的通用参数，只覆盖 benchmark 路径和排除项。

### 2. CC-MINI 配置

CC-MINI 用于 runtime repair 和 fallback agent。它使用单独的 `.cc-mini.toml`，可以和主转译流程使用不同的 provider、API key、base URL 和 model。

创建本地私有配置：

```bash
cp .cc-mini.example.toml .cc-mini.toml
```

编辑 `.cc-mini.toml`：

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

`.cc-mini.toml` 已加入 `.gitignore`。

## 运行 Arraylist Smoke

smoke 使用 `benchmarks/arraylist/`，输出到 `Output/arraylist_smoke_current/`：

```bash
./scripts/smoke_test.sh
```

## 运行其他公开 Benchmark

创建好 `configs/config.ini` 和 `.cc-mini.toml` 后，可以直接运行较大的公开 benchmark 配置：

```bash
cd Tool
./run.sh ../configs/config_c_algorithm.ini
./run.sh ../configs/config_crown.ini
```

这些运行比默认 smoke 更大，通常会消耗更多模型调用和 runtime repair 迭代。

关键输出：

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

运行结束后优先看 `report.md`。它会汇总编译/测试状态、重试、runtime repair 和主要错误类型。

## 直接运行 Tool

从仓库根目录：

```bash
cd Tool
./run.sh ../configs/config.ini
```

配置好本地 `configs/config.ini` 后，也可以直接：

```bash
cd Tool
./run.sh
```

## 正确性说明

当前流程通过 Cargo 编译、运行测试、round-trip 检查和可选 CC-MINI 修复来验证转译结果。这是工程验证，不是形式化语义等价证明。

生成的 Rust 通常面向安全和测试通过，但可能仍然比较 C-shaped，不一定是完全惯用 Rust。更惯用的 Rustification 应作为后续优化层处理。

## 密钥处理

公开前建议扫描：

```bash
rg -n --hidden "sk-|api_key|password|Bearer|token" .
```

任何进入过 Git 历史的 API key 都应视为泄露并轮换。如果要公开现有 Git 历史，需要用 `git-filter-repo` 等工具清理历史。更稳的方式是新建干净公开仓库，只提交清理后的快照。

## License

见 [LICENSE](LICENSE)。
