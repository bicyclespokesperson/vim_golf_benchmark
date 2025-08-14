#!/usr/bin/env bash

# Vim Golf LLM Benchmark Runner
# Forwards all arguments to the Python benchmark

# Change to script directory
cd "$(dirname "$0")"

uv run python -m src.main "$@"