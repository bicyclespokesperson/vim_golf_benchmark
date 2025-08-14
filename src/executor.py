import time
import tempfile
import signal
from pathlib import Path
from typing import Dict, Any
import pynvim


class TimeoutError(Exception):
    pass


class VimExecutor:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout

    def _timeout_handler(self, signum, frame):
        raise TimeoutError(f"Neovim execution timed out after {self.timeout} seconds")

    def _process_keystrokes(self, keystrokes: str) -> str:
        """Convert special key sequences to actual control characters"""
        # Common Vim key mappings
        key_mappings = {
            "<Esc>": "\x1b",  # Escape
            "<C-c>": "\x03",  # Ctrl-C
            "<C-x>": "\x18",  # Ctrl-X
            "<C-y>": "\x19",  # Ctrl-Y
            "<C-z>": "\x1a",  # Ctrl-Z
            "<C-a>": "\x01",  # Ctrl-A
            "<C-b>": "\x02",  # Ctrl-B
            "<C-d>": "\x04",  # Ctrl-D
            "<C-e>": "\x05",  # Ctrl-E
            "<C-f>": "\x06",  # Ctrl-F
            "<C-g>": "\x07",  # Ctrl-G
            "<C-h>": "\x08",  # Ctrl-H (Backspace)
            "<C-i>": "\x09",  # Ctrl-I (Tab)
            "<C-j>": "\x0a",  # Ctrl-J (Enter)
            "<C-k>": "\x0b",  # Ctrl-K
            "<C-l>": "\x0c",  # Ctrl-L
            "<C-m>": "\x0d",  # Ctrl-M (Enter)
            "<C-n>": "\x0e",  # Ctrl-N
            "<C-o>": "\x0f",  # Ctrl-O
            "<C-p>": "\x10",  # Ctrl-P
            "<C-q>": "\x11",  # Ctrl-Q
            "<C-r>": "\x12",  # Ctrl-R
            "<C-s>": "\x13",  # Ctrl-S
            "<C-t>": "\x14",  # Ctrl-T
            "<C-u>": "\x15",  # Ctrl-U
            "<C-v>": "\x16",  # Ctrl-V
            "<C-w>": "\x17",  # Ctrl-W
            "<CR>": "\x0d",  # Carriage return
            "<Tab>": "\x09",  # Tab
            "<BS>": "\x08",  # Backspace
            "<Up>": "\x1b[A",  # Arrow up
            "<Down>": "\x1b[B",  # Arrow down
            "<Right>": "\x1b[C",  # Arrow right
            "<Left>": "\x1b[D",  # Arrow left
        }

        processed = keystrokes
        for key_seq, control_char in key_mappings.items():
            processed = processed.replace(key_seq, control_char)

        return processed

    def execute_challenge(
        self, initial: str, target: str, keystrokes: str
    ) -> Dict[str, Any]:
        start_time = time.time()

        # Set up timeout signal
        old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.timeout)

        try:
            print(f"        Creating temp file...")
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write(initial)
                temp_file = Path(f.name)

            print(f"        Starting Neovim...")
            nvim = pynvim.attach("child", argv=["nvim", "--embed", "--headless"])

            try:
                print(f"        Loading file: {temp_file}")
                nvim.command(f"edit {temp_file}")

                print(f"        Sending keystrokes: {repr(keystrokes)}")
                # Convert special key sequences to actual control characters
                processed_keystrokes = self._process_keystrokes(keystrokes)
                nvim.input(processed_keystrokes)

                print(f"        Waiting for completion...")
                time.sleep(0.1)

                print(f"        Reading buffer...")
                lines = nvim.current.buffer[:]
                result = "\n".join(lines)

                # Compare with whitespace stripped
                passed = result.strip() == target.strip()
                execution_time = int((time.time() - start_time) * 1000)

                print(f"        Result: {repr(result)}")
                print(f"        Expected: {repr(target)}")
                print(f"        Passed: {passed}")

                return {
                    "passed": passed,
                    "keystrokes": keystrokes,
                    "keystroke_count": len(keystrokes),
                    "execution_time_ms": execution_time,
                    "result": result,
                    "error": None,
                }

            finally:
                print(f"        Cleaning up Neovim...")
                try:
                    nvim.close()
                except:
                    pass
                temp_file.unlink(missing_ok=True)
                print(f"        Cleanup complete")

        except TimeoutError as e:
            execution_time = int((time.time() - start_time) * 1000)
            print(f"        ⚠️  Execution timed out after {self.timeout} seconds")
            return {
                "passed": False,
                "keystrokes": keystrokes,
                "keystroke_count": len(keystrokes),
                "execution_time_ms": execution_time,
                "result": None,
                "error": str(e),
            }

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return {
                "passed": False,
                "keystrokes": keystrokes,
                "keystroke_count": len(keystrokes),
                "execution_time_ms": execution_time,
                "result": None,
                "error": str(e),
            }
        finally:
            # Restore signal handler and disable alarm
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
