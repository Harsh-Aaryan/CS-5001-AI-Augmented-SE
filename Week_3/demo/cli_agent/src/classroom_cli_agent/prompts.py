from __future__ import annotations


def program_prompt(desc: str, existing: str) -> str:
    return (
        "You are a software engineer. Write a single Python module that satisfies the description.\n"
        "Return ONLY the full module content.\n"
        "IMPORTANT:\n"
        "- Output raw Python only\n"
        "- Do NOT use Markdown\n"
        "- Do NOT use ``` fences\n"
        "- Do NOT include explanations\n"
        "Constraints:\n"
        "- Python standard library only\n"
        "- Include docstrings\n"
        "- Keep the design minimal\n\n"
        f"DESCRIPTION:\n{desc}\n\n"
        "EXISTING MODULE (may be empty):\n"
        f"{existing}\n"
    )


def tests_prompt(desc: str, module_path: str, module_code: str, existing_tests: str) -> str:
    return (
        "You are a QA engineer. Write pytest tests for the described module.\n"
        "Return ONLY the full test file content.\n"
        "IMPORTANT:\n"
        "- Output raw Python only\n"
        "- Do NOT use Markdown\n"
        "- Do NOT use ``` fences\n"
        "- Do NOT include explanations\n"
        "Constraints:\n"
        "- Use pytest\n"
        "- Aim for high line coverage of the target module\n"
        "- Do not modify production code in this step\n\n"
        f"DESCRIPTION:\n{desc}\n\n"
        f"TARGET MODULE PATH: {module_path}\n\n"
        "TARGET MODULE CODE:\n"
        f"{module_code}\n\n"
        "EXISTING TESTS (may be empty):\n"
        f"{existing_tests}\n"
    )


def scaffold_prompt(desc: str, out_dir: str, existing_tree: str) -> str:
    return (
        "You are a software engineer. Create a multi-file project scaffold that satisfies the description.\n"
        "Return ONLY valid JSON.\n"
        "IMPORTANT:\n"
        "- Output JSON only (no Markdown, no explanations)\n"
        "- Do NOT wrap in ``` fences\n"
        "- Paths must be relative, use forward slashes\n"
        "- Do NOT use absolute paths\n"
        "- Do NOT include '..' in paths\n"
        "\n"
        "JSON schema (required):\n"
        "{\n"
        "  \"files\": [\n"
        "    {\"path\": \"relative/path.ext\", \"content\": \"file contents...\"}\n"
        "  ]\n"
        "}\n"
        "\n"
        "Guidance:\n"
        "- Include an entrypoint module in src/ (for Flask prefer src/app.py with create_app())\n"
        "- Put routes in src/routes/, services in src/services/, templates in src/templates/ when relevant\n"
        "- Keep dependencies minimal; use common project layout\n"
        "\n"
        f"OUTPUT ROOT (all files must be under this directory): {out_dir}\n\n"
        f"DESCRIPTION:\n{desc}\n\n"
        "EXISTING TREE (paths under output root, may be empty):\n"
        f"{existing_tree}\n"
    )
