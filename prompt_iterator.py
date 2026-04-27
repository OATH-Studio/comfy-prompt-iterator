"""
Prompt Iterator Node for ComfyUI
-----------------------------------------
Loads prompts from a text file and runs them sequentially, one per line.

"control_after_generate" controls which prompt is picked on the NEXT run:

    fixed      — always use the same prompt
    increment  — step forward one prompt each run
    decrement  — step backward one prompt each run
    randomize  — pick a random prompt each run

Queue 10 runs with increment and it walks through prompts automatically.

Install:
    Drop this folder into ComfyUI/custom_nodes/ and restart.
    Node appears under "utils/prompt" as "Prompt Iterator"
"""

import os
import random as _random


CONTROL_MODES = ["fixed", "increment", "decrement", "randomize"]

_state: dict[str, int] = {}


def get_prompt_texts_dir():
    """Get the prompt_texts directory path relative to this script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "prompt_texts")



def _scan_prompt_files() -> list[str]:
    """Get all .txt files from prompt_texts directory."""
    prompt_dir = get_prompt_texts_dir()
    if not os.path.isdir(prompt_dir):
        return []
    all_files = [f for f in os.listdir(prompt_dir) if os.path.isfile(os.path.join(prompt_dir, f))]
    return sorted([f for f in all_files if f.endswith(".txt")], key=lambda p: p.lower())


def _load_prompt_file(filepath: str) -> list[str]:
    """Load a text file and return each non-empty line as a prompt."""
    try:
        prompt_dir = get_prompt_texts_dir()
        full_path = os.path.join(prompt_dir, filepath)
        with open(full_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]
            return [line for line in lines if line]  # Filter empty lines
    except Exception as e:
        print(f"[PromptIterator] ERROR loading {filepath}: {e}")
        return []



class PromptIterator:
    """Node that loads prompts from a text file and outputs one at a time."""

    @classmethod
    def INPUT_TYPES(cls):
        all_prompts = _scan_prompt_files()

        return {
            "required": {
                "prompt_file": (all_prompts if all_prompts else ["(no prompt files found)"], {"default": all_prompts[0] if all_prompts else ""}),
                "control_after_generate": (CONTROL_MODES, {"default": "increment"}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "INT", "INT")
    RETURN_NAMES = ("prompt_text", "current_index", "total_prompts")
    FUNCTION     = "load_prompt"
    CATEGORY     = "utils/prompt"
    DESCRIPTION  = (
        "Loads prompts from a text file, one per line. "
        "control_after_generate advances the prompt selection after each run: "
        "fixed / increment / decrement / randomize."
    )

    @classmethod
    def IS_CHANGED(cls, prompt_file, control_after_generate, unique_id="default"):
        if control_after_generate == "fixed":
            return f"{prompt_file}"
        import random

        return random.random()

    def load_prompt(self, prompt_file, control_after_generate, unique_id="default"):
        all_prompts = _scan_prompt_files()

        if not all_prompts:
            print("[PromptIterator] No prompt files found")
            return ("", 0, 0)

        # Find the index of the selected file in the list
        file_idx = all_prompts.index(prompt_file) if prompt_file in all_prompts else 0
        total_files = len(all_prompts)

        prompts = _load_prompt_file(prompt_file)

        if not prompts:
            print(f"[PromptIterator] No prompts found in: {prompt_file!r}")
            return ("", file_idx, total_files)

        # Track line index separately per file using unique_id + filename
        state_key = f"{unique_id}:{prompt_file}"
        total_lines = len(prompts)

        if state_key not in _state:
            _state[state_key] = 0

        line_idx = _state[state_key]

        # Apply control mode to advance the line index
        if control_after_generate == "fixed":
            pass  # Keep current line
        elif control_after_generate == "increment":
            _state[state_key] = (line_idx + 1) % total_lines
        elif control_after_generate == "decrement":
            _state[state_key] = (line_idx - 1) % total_lines
        elif control_after_generate == "randomize":
            _state[state_key] = _random.randint(0, total_lines - 1)

        prompt_text = prompts[line_idx]

        print(f"[PromptIterator] [{file_idx + 1}/{total_files}] {prompt_file} | " f"running line {line_idx + 1}/{total_lines}")

        return (prompt_text, line_idx + 1, total_lines)


# ── registration ──────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {"PromptIterator": PromptIterator}
NODE_DISPLAY_NAME_MAPPINGS = {"PromptIterator": "Prompt Iterator"}
