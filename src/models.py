from abc import ABC, abstractmethod
from typing import Optional
import os
import ollama
import anthropic


def create_vim_prompt(initial: str, target: str) -> str:
    return f"""Transform this text from START to END using Neovim keystrokes only.

Prioritize accuracy first, then minimal keystrokes.

Note: 
- Use <Esc> to represent the escape key when needed
- Use <C-x> format for control keys (e.g., <C-c>, <C-x>, <C-y>)
- Use <CR> for enter, <Tab> for tab, <BS> for backspace
- Use <Up>, <Down>, <Left>, <Right> for arrow keys
- Leading/trailing whitespace is ignored when comparing results
- You can put your thinking inside <thinking></thinking> tags if helpful

Example:
START: apple
END: APPLE
Answer: gUiw

START:
{initial}

END:
{target}

Return only the vim keystrokes needed to make this transformation (and any thinking you want to do). Do not include any explanation or additional text."""


def parse_vim_response(
    response: str, model_name: str = "unknown", initial: str = "", target: str = ""
) -> str:
    """Parse model response, extracting keystrokes and removing reasoning/thinking content"""
    import re

    original_response = response.strip()

    # Always log the full response
    save_response_log(model_name, original_response, initial, target)

    # Extract vim commands from various reasoning patterns
    result = extract_vim_commands(original_response)
    return result


def extract_vim_commands(content: str) -> str:
    """Extract vim commands from model response, removing thinking/reasoning content"""
    import re

    original_content = content

    # First, try to extract content from code blocks (```...```)
    code_block_match = re.search(
        r"```(?:vim|bash|shell)?\s*(.*?)```", content, re.DOTALL | re.IGNORECASE
    )
    if code_block_match:
        extracted = code_block_match.group(1).strip()
        if extracted:
            return extracted

    # Remove thinking tags and extract what comes after
    thinking_match = re.search(
        r"<thinking>(.*?)</thinking>\s*(.*?)$", content, re.DOTALL | re.IGNORECASE
    )
    if thinking_match:
        after_thinking = thinking_match.group(2).strip()
        if after_thinking:
            content = after_thinking

    # Handle malformed thinking tags (unclosed)
    elif "<thinking>" in content:
        parts = content.split("<thinking>", 1)
        if len(parts) > 1:
            # Look for actual vim commands after the thinking part
            thinking_part = parts[1]
            # Try to find vim-like patterns after reasoning
            lines = thinking_part.split("\n")
            vim_lines = []
            found_commands = False

            for line in lines:
                stripped = line.strip()
                # Look for lines that look like vim commands
                if (
                    re.match(r"^[a-zA-Z0-9:<>\\$%/\-\.\*\+\{\}\[\]\(\)\s]+$", stripped)
                    and len(stripped) < 50
                    and stripped
                    and not any(
                        word in stripped.lower()
                        for word in ["thinking", "need to", "will use", "can do"]
                    )
                ):
                    vim_lines.append(stripped)
                    found_commands = True
                elif found_commands and not stripped:
                    break  # Stop at empty line after finding commands

            if vim_lines:
                content = "\n".join(vim_lines)

    # Remove other reasoning patterns
    patterns = [
        r"Let me think.*?:(.*?)(?=\n\n|\nFinal|Answer:)",
        r"Reasoning:(.*?)(?=\n\n|\nAnswer:|\nConclusion:)",
        r"I need to.*?(?=\n[A-Z<])",  # Remove explanatory sentences
        r".*?Answer:\s*",  # Remove everything before "Answer:"
        r".*?Keystrokes:\s*",  # Remove everything before "Keystrokes:"
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match and match.group(1):
            content = match.group(1).strip()
            break

    # Clean up the result
    content = content.strip()

    # Remove any remaining non-vim content at the start
    lines = content.split("\n")
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            # Skip explanatory text
            if any(
                phrase in stripped.lower()
                for phrase in [
                    "i need to",
                    "let me",
                    "first",
                    "then",
                    "this will",
                    "we can",
                    "the goal",
                    "to do this",
                    "explanation",
                    "approach",
                ]
            ):
                continue
            clean_lines.append(stripped)

    result = "\n".join(clean_lines) if clean_lines else content

    return result or original_content.strip()


def save_response_log(
    model_name: str, response: str, initial: str = "", target: str = ""
) -> None:
    """Save all model responses to a log file"""
    from datetime import datetime, timezone
    from pathlib import Path

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Append to response log
    log_file = logs_dir / "model_responses.log"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 60}\n")
        f.write(f"Model: {model_name}\n")
        f.write(f"Timestamp: {timestamp}\n")
        if initial and target:
            f.write(f"Transformation: {repr(initial)} -> {repr(target)}\n")
        f.write(f"{'=' * 60}\n")
        f.write(f"{response}\n")
        f.write(f"{'=' * 60}\n")


def save_thinking_log(
    model_name: str, response: str, initial: str = "", target: str = ""
) -> None:
    """Save responses containing thinking tags to a log file (legacy function)"""
    # This function is kept for backwards compatibility but now just calls save_response_log
    save_response_log(model_name, response, initial, target)


class ModelProvider(ABC):
    @abstractmethod
    def get_vim_commands(self, initial: str, target: str) -> str:
        pass


class OllamaProvider(ModelProvider):
    def __init__(self, model: str, host: Optional[str] = None):
        self.model = model
        self.client = ollama.Client(host=host) if host else ollama.Client()

    def get_vim_commands(self, initial: str, target: str) -> str:
        prompt = create_vim_prompt(initial, target)

        try:
            print(f"      Sending prompt to {self.model}...")
            response = self.client.chat(
                model=self.model, messages=[{"role": "user", "content": prompt}]
            )
            print(f"      Received response from {self.model}")
            return parse_vim_response(
                response["message"]["content"], self.model, initial, target
            )
        except Exception as e:
            raise Exception(f"Failed to get vim commands from {self.model}: {e}")


class ClaudeProvider(ModelProvider):
    def __init__(self, model: str, api_key: Optional[str] = None):
        self.model = model
        self.client = anthropic.Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )

    def get_vim_commands(self, initial: str, target: str) -> str:
        prompt = create_vim_prompt(initial, target)

        try:
            print(f"      Sending prompt to {self.model}...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            print(f"      Received response from {self.model}")
            return parse_vim_response(
                response.content[0].text, self.model, initial, target
            )
        except Exception as e:
            raise Exception(f"Failed to get vim commands from {self.model}: {e}")


class TestProvider(ModelProvider):
    """Test provider that returns hardcoded correct answers for verification"""

    def __init__(self, model: str = "test"):
        self.model = model
        # Known correct answers for our test challenges
        self.answers = {
            ("Remove me\nKeep this\nAnd this", "Keep this\nAnd this"): "ggdd",
            ("hello world", "world hello"): "dwwa <Esc>p",
            ("a,b,c\n1,2,3", "a|b|c\n1|2|3"): ":%s/,/|/g\n",
            ("first\nsecond\nthird\nfourth", "fourth\nthird\nsecond\nfirst"): "Gdap",
            ("hello world vim", '"hello" "world" "vim"'): ':%s/\\w\\+/"&"/g\n',
            (
                "# Introduction\n# Normal mode\n# Command Line mode\n# Visual mode",
                "* [Introduction](#introduction)\n* [Normal mode](#normal-mode)\n* [Command Line mode](#command-line-mode)\n* [Visual mode](#visual-mode)",
            ): ":%s/.*/placeholder/g\n",
        }

    def get_vim_commands(self, initial: str, target: str) -> str:
        print(f"      Test provider returning hardcoded answer...")

        # Handle connection test
        if initial == "test" and target == "test":
            response = "test_successful"
        else:
            key = (initial, target)
            if key in self.answers:
                response = self.answers[key]
            else:
                raise Exception(
                    f"No hardcoded answer for transformation: {initial!r} -> {target!r}"
                )

        # Log the response like other providers do
        return parse_vim_response(response, self.model, initial, target)


def create_model_provider(model: str) -> ModelProvider:
    if model == "test":
        return TestProvider(model)
    elif ":" in model:
        return OllamaProvider(model)
    elif model.startswith("claude-"):
        return ClaudeProvider(model)
    else:
        raise ValueError(
            f"Unsupported model format: {model}. Use 'test' for hardcoded answers, 'model:tag' for Ollama, or 'claude-*' for Claude models."
        )
