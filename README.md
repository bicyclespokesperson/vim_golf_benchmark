# Vim Golf LLM Benchmark

A comprehensive benchmark for testing Large Language Model performance on vim golf challenges.

## 🎯 What is Vim Golf?

Vim golf is the art of accomplishing text editing tasks using the fewest possible keystrokes in vim. This benchmark tests how well LLMs can generate efficient vim command sequences.

## 🚀 Quick Start

```bash
# Test with hardcoded correct answers (verification)
./run_benchmark.sh --models test

# Test with local Ollama models
./run_benchmark.sh --models gemma3:latest

# Test with Claude models (requires ANTHROPIC_API_KEY)
./run_benchmark.sh --models claude-3-5-sonnet-20241022

# Test multiple models
./run_benchmark.sh --models test,gemma3:latest,claude-3-5-haiku-20241022

# Generate report from existing results
./run_benchmark.sh --report-only
```

## 📊 Latest Results

See [REPORT.md](REPORT.md) for the latest benchmark results and model comparisons.

## 🏗️ Features

- **Multi-provider support**: Ollama (local), Claude (API), and test verification
- **Neovim integration**: Real vim execution with timeout protection
- **Comprehensive reporting**: Detailed per-challenge breakdowns and summaries
- **Control key support**: Full support for `<C-x>`, `<Esc>`, `<CR>`, etc.
- **Whitespace handling**: Strips leading/trailing whitespace in comparisons
- **Early failure detection**: Models with connection issues fail fast

## 🧩 Challenge Types

The benchmark includes three starter challenges:

1. **Delete first line** (Easy): Remove the first line of text
2. **Swap two words** (Medium): Exchange positions of two words
3. **CSV to pipe conversion** (Hard): Replace commas with pipes using regex

## 📁 Project Structure

```
vim-golf-benchmark/
├── README.md              # This file
├── REPORT.md              # Latest benchmark results (auto-generated)
├── challenges.json        # Challenge definitions
├── run_benchmark.sh       # Main execution script
├── src/                   # Source code
│   ├── main.py           # CLI interface
│   ├── models.py         # Model provider interfaces
│   ├── executor.py       # Neovim execution engine
│   └── reporter.py       # Report generation
├── outputs/              # JSON results by model and timestamp
└── logs/                 # LLM Logs
```

## 🔧 Adding New Models

To add support for a new model provider:

1. Create a new provider class inheriting from `ModelProvider` in `src/models.py`
2. Implement the `get_vim_commands(initial, target)` method
3. Add detection logic in `create_model_provider()`

## 📝 Output Format

Results are saved as timestamped JSON files in `outputs/` with:

- Model accuracy and efficiency metrics
- Per-challenge results with keystrokes and execution details
- Error messages and timeout information

## 📊 Scoring

- **Primary metric**: Accuracy (% of challenges solved correctly)
- **Secondary metric**: Average keystrokes for successful attempts
- **Efficiency comparison**: Ratio to known optimal solutions

## 🔒 Requirements

- Python 3.10+
- uv (package manager)
- Neovim
- Ollama (for local models)
- ANTHROPIC_API_KEY environment variable (for Claude models)

## 🎮 Vim Key Support

The benchmark supports all standard vim keystrokes:

- Control keys: `<C-x>`, `<C-y>`, `<C-c>`, etc.
- Special keys: `<Esc>`, `<CR>`, `<Tab>`, `<BS>`
- Normal vim commands: `gg`, `dd`, `:%s/pattern/replacement/g`, etc.

## 🚧 Development

```bash
# Run with debug output
./run_benchmark.sh --models test

# Generate only reports
./run_benchmark.sh --report-only

# Add new challenges to challenges.json
# Test verification works with known correct answers
```

## 📈 Contributing

1. Add new challenges to `challenges.json`
2. Test with the `test` model to verify vim execution works
3. Update the benchmark and commit the new `REPORT.md`

---

_This benchmark helps evaluate and improve LLM understanding of vim commands for efficient text editing._
