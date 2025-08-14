#!/usr/bin/env python3

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
import ollama

from .models import create_model_provider
from .executor import VimExecutor
from .reporter import Reporter


def get_available_models() -> str:
    """Get formatted list of available models for help text"""
    try:
        ollama_models = ollama.list()
        model_names = [model.model for model in ollama_models.models]
        if model_names:
            ollama_list = ", ".join(model_names)
        else:
            ollama_list = "(none available - start ollama server)"
    except Exception:
        ollama_list = "(unavailable - start ollama server)"

    claude_models = (
        "claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, claude-3-opus-20240229"
    )

    return f"""Available models:
  • Ollama: {ollama_list}
  • Claude: {claude_models}
  • Test: test (hardcoded answers for verification)
  
Model routing:
  • Models with ':' (e.g. gemma:2b) → Ollama API
  • Models starting with 'claude-' → Anthropic API (requires ANTHROPIC_API_KEY)
  • 'test' → Built-in test provider"""


def load_challenges(challenges_file: Path) -> List[Dict[str, Any]]:
    with open(challenges_file) as f:
        return json.load(f)


def run_benchmark_for_model(
    model: str,
    challenges: List[Dict[str, Any]],
    executor: VimExecutor,
    outputs_dir: Path,
) -> bool:
    print(f"Running benchmark for model: {model}")

    try:
        model_provider = create_model_provider(model)
    except Exception as e:
        print(f"  ✗ Failed to initialize model provider: {e}")
        return False

    results = []
    total_time = 0
    passed_count = 0
    total_keystrokes = 0

    for i, challenge in enumerate(challenges, 1):
        print(f"  Challenge {i}/{len(challenges)}: {challenge['title']}")

        try:
            print(f"    Querying model for keystrokes...")
            model_start_time = time.time()
            keystrokes = model_provider.get_vim_commands(
                challenge["initial"], challenge["target"]
            )
            model_end_time = time.time()
            model_time_ms = int((model_end_time - model_start_time) * 1000)
            print(
                f"    Generated keystrokes: {repr(keystrokes)} (model took {model_time_ms}ms)"
            )

            print(f"    Executing in Neovim...")
            result = executor.execute_challenge(
                challenge["initial"], challenge["target"], keystrokes
            )

            result["id"] = challenge["id"]
            result["model_time_ms"] = model_time_ms
            results.append(result)

            total_time += result["execution_time_ms"] + model_time_ms
            if result["passed"]:
                passed_count += 1
                total_keystrokes += result["keystroke_count"]
                print(f"    ✓ Passed in {result['keystroke_count']} keystrokes")
            else:
                print(f"    ✗ Failed: {result.get('error', 'Output mismatch')}")

        except Exception as e:
            print(f"    ✗ Error: {e}")
            results.append(
                {
                    "id": challenge["id"],
                    "passed": False,
                    "keystrokes": "",
                    "keystroke_count": 0,
                    "execution_time_ms": 0,
                    "model_time_ms": 0,
                    "result": None,
                    "error": str(e),
                }
            )

    accuracy = passed_count / len(challenges) if challenges else 0
    avg_keystrokes = total_keystrokes / passed_count if passed_count > 0 else 0

    summary = {
        "accuracy": accuracy,
        "avg_keystrokes": avg_keystrokes,
        "total_time_ms": total_time,
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_data = {
        "model": model,
        "timestamp": timestamp,
        "challenges": results,
        "summary": summary,
    }

    output_file = outputs_dir / f"{model}_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"  Results saved to: {output_file}")
    print(f"  Accuracy: {accuracy:.1%}, Avg keystrokes: {avg_keystrokes:.1f}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Vim Golf LLM Benchmark",
        epilog=get_available_models(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--models",
        help="Comma-separated list of models to test",
    )
    parser.add_argument(
        "--challenges", default="challenges.json", help="Path to challenges JSON file"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Skip benchmark and only generate report",
    )
    parser.add_argument(
        "--output-markdown", help="Save report as markdown to specified file"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    challenges_file = project_root / args.challenges
    outputs_dir = project_root / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    if args.report_only:
        reporter = Reporter(outputs_dir)
        reporter.generate_report()  # Show all available results

        # Always save markdown report with all models
        report_file = project_root / "REPORT.md"
        reporter.save_markdown_report(report_file)  # All models
        print(f"Report saved to: {report_file}")

        if args.output_markdown:
            reporter.save_markdown_report(Path(args.output_markdown))
            print(f"Additional report saved to: {args.output_markdown}")
        return

    if not args.models:
        print("Error: --models is required when not using --report-only")
        print()
        print(get_available_models())
        return

    if not challenges_file.exists():
        print(f"Error: Challenges file not found: {challenges_file}")
        return

    challenges = load_challenges(challenges_file)
    executor = VimExecutor()
    models = [model.strip() for model in args.models.split(",")]

    print(
        f"Running benchmark with {len(challenges)} challenges for {len(models)} model(s)"
    )
    print()

    successful_models = []
    for model in models:
        success = run_benchmark_for_model(model, challenges, executor, outputs_dir)
        if success:
            successful_models.append(model)
        print()

    if not successful_models:
        print("No models completed successfully.")
        return

    print("Generating report...")
    reporter = Reporter(outputs_dir)
    reporter.generate_report(
        models_filter=successful_models
    )  # Console: current run only

    # Always save markdown report with ALL available models
    report_file = project_root / "REPORT.md"
    reporter.save_markdown_report(report_file)  # REPORT.md: all models
    print(f"Report saved to: {report_file}")

    if args.output_markdown:
        reporter.save_markdown_report(
            Path(args.output_markdown), models_filter=successful_models
        )
        print(f"Additional report saved to: {args.output_markdown}")


if __name__ == "__main__":
    main()
