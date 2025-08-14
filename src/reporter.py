import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.text import Text


class Reporter:
    def __init__(self, outputs_dir: Path, challenges_file: Optional[Path] = None):
        self.outputs_dir = outputs_dir
        self.console = Console()
        self.challenges_file = challenges_file or outputs_dir.parent / "challenges.json"
        self.challenges_data = self._load_challenges()

    def _load_challenges(self) -> Dict[str, Any]:
        try:
            if self.challenges_file.exists():
                with open(self.challenges_file) as f:
                    challenges_list = json.load(f)
                    return {c["id"]: c for c in challenges_list}
        except Exception:
            pass
        return {}

    def _truncate(self, text: str, max_len: int = 100) -> str:
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    def get_latest_results(self) -> Dict[str, Dict[str, Any]]:
        latest_files = {}

        if not self.outputs_dir.exists():
            return latest_files

        for file_path in self.outputs_dir.glob("*.json"):
            try:
                model_name = file_path.stem.rsplit("_", 1)[0]
                timestamp = file_path.stem.rsplit("_", 1)[1]

                if (
                    model_name not in latest_files
                    or timestamp > latest_files[model_name]["timestamp"]
                ):
                    with open(file_path) as f:
                        data = json.load(f)
                        latest_files[model_name] = data
            except (ValueError, json.JSONDecodeError, IndexError):
                continue

        return latest_files

    def generate_report(self, models_filter: Optional[List[str]] = None) -> None:
        results = self.get_latest_results()

        # Filter results to only include specified models if provided
        if models_filter:
            results = {k: v for k, v in results.items() if k in models_filter}

        if not results:
            self.console.print("[red]No results found in outputs directory[/red]")
            return

        self.console.print("\n[bold]Vim Golf LLM Benchmark Report[/bold]")
        self.console.print("=" * 50)

        # Detailed per-challenge results
        if results:
            first_result = list(results.values())[0]
            challenges = first_result.get("challenges", [])

            for challenge in challenges:
                challenge_id = challenge.get("id", "unknown")
                challenge_info = self.challenges_data.get(challenge_id, {})

                self.console.print(
                    f"\n[bold cyan]Challenge: {challenge_id}[/bold cyan]"
                )

                # Show challenge details
                if challenge_info:
                    initial = self._truncate(repr(challenge_info.get("initial", "N/A")))
                    target = self._truncate(repr(challenge_info.get("target", "N/A")))
                    self.console.print(f"  Input: {initial}")
                    self.console.print(f"  Expected: {target}")

                # Show each model's attempt
                for model_name, data in results.items():
                    model_challenges = {c["id"]: c for c in data.get("challenges", [])}
                    if challenge_id in model_challenges:
                        c = model_challenges[challenge_id]
                        keystrokes = self._truncate(repr(c.get("keystrokes", "N/A")))
                        actual = self._truncate(repr(c.get("result", "N/A")))

                        if c.get("passed"):
                            status = f"✓ {c.get('keystroke_count', 0)} keystrokes"
                            style = "green"
                        else:
                            status = "✗ Failed"
                            style = "red"

                        self.console.print(
                            f"  [{style}]{model_name}: {status}[/{style}]"
                        )
                        self.console.print(f"    Keystrokes: {keystrokes}")
                        self.console.print(f"    Actual: {actual}")
                        if c.get("error"):
                            self.console.print(f"    Error: {c['error']}")
                    else:
                        self.console.print(f"  [dim]{model_name}: No result[/dim]")

        # Summary table at the end
        self.console.print(f"\n[bold]Summary[/bold]")
        summary_table = Table()
        summary_table.add_column("Model", style="cyan")
        summary_table.add_column("Accuracy", style="green")
        summary_table.add_column("Avg Keystrokes", style="yellow")
        summary_table.add_column("Total Time (ms)", style="blue")

        for model_name, data in results.items():
            summary = data.get("summary", {})
            accuracy = f"{summary.get('accuracy', 0):.1%}"
            avg_keystrokes = f"{summary.get('avg_keystrokes', 0):.1f}"
            total_time = f"{summary.get('total_time_ms', 0)}"

            summary_table.add_row(model_name, accuracy, avg_keystrokes, total_time)

        self.console.print(summary_table)

    def save_markdown_report(
        self, output_file: Path, models_filter: Optional[List[str]] = None
    ) -> None:
        results = self.get_latest_results()

        # Filter results to only include specified models if provided
        if models_filter:
            results = {k: v for k, v in results.items() if k in models_filter}

        if not results:
            return

        lines = ["# Vim Golf LLM Benchmark Report\n"]

        lines.append("## Summary\n")
        lines.append("| Model | Accuracy | Avg Keystrokes | Total Time (ms) |")
        lines.append("|-------|----------|----------------|-----------------|")

        for model_name, data in results.items():
            summary = data.get("summary", {})
            accuracy = f"{summary.get('accuracy', 0):.1%}"
            avg_keystrokes = f"{summary.get('avg_keystrokes', 0):.1f}"
            total_time = f"{summary.get('total_time_ms', 0)}"
            lines.append(
                f"| {model_name} | {accuracy} | {avg_keystrokes} | {total_time} |"
            )

        lines.append("\n## Per-Challenge Results\n")

        if results:
            first_result = list(results.values())[0]
            challenges = first_result.get("challenges", [])

            header = "| Challenge |"
            separator = "|-----------|"
            for model_name in results.keys():
                header += f" {model_name} |"
                separator += "---------|"

            lines.append(header)
            lines.append(separator)

            for challenge in challenges:
                challenge_id = challenge.get("id", "unknown")
                row = f"| {challenge_id} |"

                for model_name, data in results.items():
                    model_challenges = {c["id"]: c for c in data.get("challenges", [])}
                    if challenge_id in model_challenges:
                        c = model_challenges[challenge_id]
                        if c.get("passed"):
                            status = f"✓ ({c.get('keystroke_count', 0)})"
                        else:
                            status = "✗"
                    else:
                        status = "?"
                    row += f" {status} |"

                lines.append(row)

        output_file.write_text("\n".join(lines))
