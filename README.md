# MinsC2Rust

**MinsC2Rust** is an LLM-driven framework for automated, scalable, and safe C-to-Rust project-level transpilation. It (1) analyzes function dependencies to orchestrate a transpilation schedule of C functions, (2) decomposes large C projects into self-contained C function units, (3) adopts an iterative LLM-driven transpilation process with dependency contexts and compilation error-aware to transpile C function units to Rust, and (4) reconstructs the complete Rust project while preserving the original architecture.

> 🔍 **Key Highlights:**
> - 98.8% compilation success rate  
> - 54.3% test function execution correctness  
> - 100.0% safe lines of code coverage  
> - 95.8% safe references ratio  
> - Outperforms 4 state-of-the-art competitors (Crown, Laertes, Flourine, Vert)

---

## 🌐 Project Structure

```
MinsC2Rust/
├── Output/                 # Transpiled results and metrics
├── Tool/                   # Core transpilation tools
├── analysis/               # Analysis scripts and evaluation results
├── benchmarks/             # Benchmark source projects (C-Algorithm, Crown)
├── comparisons/            # Output comparisons with competitors
├── run.sh                  # Entry point script for the full pipeline
├── clean.sh                # Project cleanup script
├── run_docker.sh           # Docker execution wrapper
└── README.md               # This documentation file
```

---

## 🧠 Core Methodology

MinsC2Rust follows a **divide-transpile-reconstruct** paradigm:

1. **Divide**: Decompose C codebase into independent function units with dependency analysis.
2. **Transpile**: Iteratively transpile function units using an LLM with error-aware recovery.
3. **Reconstruct**: Reassemble these Rust function units into a full Rust project while preserving architecture.


---

## 📊 Benchmarks

- **C-Algorithm**: Classic algorithmic C programs.
- **Crown**: Real-world C codebase.


---

## 🚀 Quick Start

### Step 1: Build Docker Image

```bash
cd Tool
docker build -t minsc2rust -f ./Dockerfile .
cd ..
./run_docker.sh
```

---

### Step 2: Run Transpilation

**Explanation of Scripts:**

* run.sh: Performs callgraph-based transpilation orchestration, self-contained function unit construction, and LLM-based function transpilation. It generates results.json containing all successfully transpiled Rust function units.

* run_post_process.sh: Reconstructs the full Rust project from results.json, preserving the architecture. It outputs the final project and writes metrics to metrics.csv.

You can run the transpilation and post-processing for each benchmark:

```bash
cd /app/Tool
# C-Algorithm benchmark
./run.sh Tool_py/configs/config_c_algorithm.ini
./run_post_process.sh Tool_py/configs/config_c_algorithm.ini

# Crown benchmark
./run.sh Tool_py/configs/config_crown.ini
./run_post_process.sh Tool_py/configs/config_crown.ini

# Merge metrics from both benchmarks
cd /app/Output
python3 merge_metrics.py
```

Alternatively, you can run the full pipeline in one step:

```bash
cd /app && ./run.sh
```

---

### 🔎 Output Structure

After transpilation, the output directory contains:

```
Output/c_algorithm/
├── Output/
│   ├── test_project/             # Complete transpiled Rust project
        └── metrics.csv           # Overall Metrics
│   ├── app.log                   # Log of transpilation process
│   ├── cargo_test_result.txt     # Output of unit tests in Rust project
│   ├── compile_pass_rate.csv     # Compilation success statistics
│   ├── tests_pass_rates.csv      # Test function correctness metrics
│   ├── loc_statistics.csv        # Code coverage and LOC stats
│   ├── once_pass_rates.csv       # One-pass compilation rates
│   ├── safety.csv                # Safety metrics
│   ├── results.json              # All successfully transpiled functions
│   └── all_error_funcs_content.json # Functions that failed to transpile
```

> ⚠️ Note: Due to inherent stochasticity in LLM generation, results may vary slightly from paper-reported metrics (±5%).

This step takes a relatively long time, typically around 3 hours. We have pre-transpiled a result, which is available at: `/app/comparisons/MinsC2Rust/`. This is also the result reported in the paper.


---

### Step 3: Prepare Results for Comparison

```bash
cd /app
cp -r ./Output/* ./comparisons/MinsC2Rust
```

---

### Step 4: Run Evaluation Scripts

Change to the analysis directory:

```bash
cd /app/analysis
```

Then run the following scripts as needed:

- **Report statistics of benchmark programs (Table 1):**

  ```bash
  python3 statistics_of_programs.py
  ```

- **Report compiled & passed stats (Table 2):**

  ```bash
  python3 correctness.py
  ```

- **Report safe lines of code coverage and safe references ratio (Table 3):**

  ```bash
  python3 safety.py
  ```

- **Evaluate the impact of different LLMs (see Tool/Tool_py/models/) (Figure 9):**

  ```bash
  python3 impact_of_llms.py
  ```

- **Evaluate the impact of iterations (change `max_retries` in the config file `config_c_algorithm.ini`) (Figure 10):**

  ```bash
  python3 impact_of_iterations.py
  ```

- **Report compilation success rate improvement with and without feedback-driven fixing (Table 4):**

  ```bash
  python3 fix_module_comparison.py
  ```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---
