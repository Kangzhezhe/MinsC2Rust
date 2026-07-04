# MinsC2Rust

**MinsC2Rust: LLM-Driven Project-Level Code Migration from C to Safe Rust** 的代码发布版本。

MinsC2Rust 是一个面向项目级 C 到 Rust 迁移的框架。它采用
**divide-transpile-reconstruct** 流程：先分析 C 项目的函数依赖关系，再构造自包含函数单元，
随后结合 LLM 与编译器反馈进行函数级转译和修复，最后重建保持原始文件组织与函数调用关系的
Rust 项目。

论文：[MinsC2Rust: LLM-driven project-level code migration from C to safe Rust](https://doi.org/10.1007/s10664-026-10905-4)

代码工件 DOI：[10.5281/zenodo.17651630](https://doi.org/10.5281/zenodo.17651630)

英文说明见 [README.md](README.md)。

## 框架

![MinsC2Rust framework](assets/framework.png)

MinsC2Rust 包含四个核心组件：

1. **CBTO：基于调用图的转译编排**
   构建函数调用图，并按照依赖关系调度函数转译顺序。
2. **SCFC：自包含函数构造**
   为每个函数构造包含函数体、类型、宏、全局变量等必要上下文的转译单元。
3. **LDFT：LLM 驱动的函数转译**
   在已有 Rust 依赖上下文中转译函数，并利用编译器反馈迭代修复编译错误。
4. **PLAR：项目级架构重建**
   对生成代码去重，并重建完整 Rust 项目。

## 仓库结构

```text
.
├── Tool/                  # 主转译流程
├── cc_mini/               # 运行时测试修复 agent
├── configs/               # 配置模板
├── benchmarks/            # 公开 C benchmark
│   ├── arraylist/         # 小规模 smoke benchmark
│   ├── c-algorithm/       # 较大的数据结构 benchmark
│   └── crown/Input/       # Crown benchmark 子集
├── scripts/               # 运行脚本
├── assets/                # README 图片
├── .cc-mini.example.toml  # CC-MINI 配置模板
└── README.md
```

生成结果默认写入 `Output/`，该目录不会进入 Git。

## 安装

测试环境：

- Python 3.12
- Rust stable 与 Cargo
- Clang / libclang
- CMake 和基础 C 编译工具
- Graphviz 与 universal-ctags
- 一个 OpenAI-compatible LLM 接口

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
git clone https://github.com/Kangzhezhe/MinsC2Rust.git
cd MinsC2Rust

curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r Tool/requirements.txt
```

## 配置

MinsC2Rust 使用两个本地配置文件，二者都被 Git 忽略。

### 主转译模型

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

### CC-MINI 运行时修复 Agent

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
```

主转译模型和 CC-MINI 可以使用不同的 provider、key、base URL 和模型。

## 快速开始

运行小规模 `arraylist` smoke benchmark：

```bash
./scripts/smoke_test.sh
```

主要输出：

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

查看一次运行结果时，建议先阅读 `Output/arraylist_smoke_current/Output/report.md`。

## 更大的 Benchmark

配置好 `configs/config.ini` 和 `.cc-mini.toml` 后，可以运行：

```bash
cd Tool
./run.sh ../configs/config_c_algorithm.ini
./run.sh ../configs/config_crown.ini
```

这些 benchmark 比 smoke 测试更大，通常需要更多 LLM 调用和修复轮次。

## 复现实验

公开仓库包含核心流程和公开 benchmark。论文报告了 C-Algorithm 和 Crown 上的实验结果，包括：

- 98.4% 编译成功率
- 42.6% 执行正确率
- 100.0% safe LOC 覆盖率
- 95.8% safe reference ratio

由于流程依赖 LLM，不同 provider、模型版本和 API 稳定性会导致输出存在差异。当前公开仓库主要用于让流程可运行、可检查；论文级归档工件见上方 artifact DOI。

对于仓库内置的 `arraylist` smoke benchmark，启用 source-level runtime repair 和
CC-MINI agent 后，可以生成 `cargo test --quiet` 全部通过的 Rust 导出工程。
这个 smoke 结果是公开流程的端到端可运行性检查，不替代上面论文级 benchmark 指标。

## 说明

- MinsC2Rust 面向项目级迁移，而不是孤立代码片段翻译。
- 当前流程优先保证编译可构建性和 Rust 安全性。
- 运行时测试和 CC-MINI 修复用于实际验证与修复，不等同于形式化语义证明。
- 生成的 Rust 在部分位置仍可能保留 C 风格；进一步 Rust idiomatic 重构属于后续阶段。

## 引用

如果在研究中使用 MinsC2Rust，请引用论文：

```bibtex
@article{kang2026minsc2rust,
  title   = {MinsC2Rust: LLM-driven project-level code migration from C to safe Rust},
  author  = {Kang, Zhehao and Zhu, Qianyu and Mou, Wenrui and Wang, Bang and Zhang, Xiaogang and Huang, Haojun},
  journal = {Empirical Software Engineering},
  year    = {2026},
  doi     = {10.1007/s10664-026-10905-4},
  url     = {https://doi.org/10.1007/s10664-026-10905-4}
}
```

如果引用本代码发布版本，也请引用代码工件：

```bibtex
@software{kang2026minsc2rust_artifact,
  title  = {MinsC2Rust: LLM-Driven Project-Level Code Migration from C to Safe Rust},
  author = {Kang, Zhehao and Zhu, Qianyu and Mou, Wenrui and Wang, Bang and Zhang, Xiaogang and Huang, Haojun},
  year   = {2026},
  doi    = {10.5281/zenodo.17651630},
  url    = {https://doi.org/10.5281/zenodo.17651630}
}
```

## License

见 [LICENSE](LICENSE)。
