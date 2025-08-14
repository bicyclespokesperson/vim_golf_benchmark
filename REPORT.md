# Vim Golf LLM Benchmark Report

## Summary

| Model                    | Accuracy | Avg Keystrokes | Total Time (ms) |
| ------------------------ | -------- | -------------- | --------------- |
| test                     | 33.3%    | 7.5            | 1319            |
| claude-sonnet-4-20250514 | 50.0%    | 9.0            | 55372           |
| gpt-oss:20b              | 83.3%    | 16.0           | 535230          |
| gemma3:latest            | 0.0%     | 0.0            | 19871           |
| granite3.2:8b            | 0.0%     | 0.0            | 31110           |

## Per-Challenge Results

| Challenge            | test   | gemma3:latest | claude-sonnet-4-20250514 | granite3.2:8b | gpt-oss:20b |
| -------------------- | ------ | ------------- | ------------------------ | ------------- | ----------- |
| delete_first_line    | ✓ (4)  | ✗             | ✓ (2)                    | ✗             | ✓ (7)       |
| swap_words           | ✓ (11) | ✗             | ✓ (12)                   | ✗             | ✓ (32)      |
| csv_to_pipe          | ✗      | ✗             | ✓ (13)                   | ✗             | ✓ (13)      |
| reverse_lines        | ✗      | ✗             | ✗                        | ✗             | ✓ (11)      |
| wrap_in_quotes       | ✗      | ✗             | ✗                        | ✗             | ✓ (17)      |
| comments_to_markdown | ✗      | ✗             | ✗                        | ✗             | ✗           |
