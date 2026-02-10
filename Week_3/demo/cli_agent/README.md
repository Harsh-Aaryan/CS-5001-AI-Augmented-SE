# Classroom CLI Agent (cca) – Ollama-hosted

Default model: `devstral-small-2:24b-cloud`

Override options:

* `--model <name>`
* `OLLAMA_MODEL` environment variable

---

## Start Ollama and pull model

```bash
ollama serve
ollama pull devstral-small-2:24b-cloud
```

---

## Install

```bash
pip install -e .
```

---

## Execution model

The CLI separates **generation**, **execution**, and **version control** into distinct actions.

### Program generation
- Writes or updates source files under `src/`.
- Triggered by `create` or as part of `full`.
- No tests are generated or executed.

### Test generation
- Writes pytest files under `tests/`.
- Triggered by `test` or as part of `full`.
- No test execution happens at this stage.

### Test execution and reporting
- Runs pytest with coverage exactly once.
- Observes results and produces a report.
- Does not rewrite source code or tests.

### Commit and push
- Explicit Git operations.

---

## Create a program

```bash
cca --repo output/demo_repo create \
  --desc "A calculator with add, subtract, multiply, divide functions" \
  --module src/calculator.py
```

Creates or updates a single Python module.

---

## Generate tests (natural language)

```
cca --repo output/demo_repo gen-tests \
  --desc "A calculator with add, subtract, multiply, divide functions" \
  --module src/calculator.py \
  --tests tests/test_calculator.py
```

```
cca --repo output/demo_repo report --fail-on-coverage "90 percent"
```

Behavior:

* Generates pytest tests for the target module.
* Executes pytest with coverage once.
* Produces a coverage-aware test report.
* Coverage is evaluated against the provided target.

No multi-pass rewriting is implied by this command. Coverage is measured, not enforced by iteration.

---

## Commit and push

```bash
cca --repo output/demo_repo commit  --message "Agent: add program + tests" --push
```

Stages all changes, commits, and optionally pushes.

---

## End-to-end

The `full` command composes **program creation**, **test generation**, and **test reporting** into a single invocation.

### Example 1

```bash
cca --repo output/demo_repo full \
  --desc "A calculator with add, subtract, multiply, divide functions" \
  --module src/calculator.py \
  --tests tests/test_calculator.py \
  --coverage "at least ninety five percent"
```

### Example 2

```bash
cca --repo output/demo_repo full \
  --desc "Create Prime Number Checker in Python" \
  --module src/prime_checker.py \
  --tests tests/test_prime_checker.py \
  --coverage "at least 80 percent"
```

### Example 3

```bash
cca --repo output/demo_flask full \
  --desc "Create a minimal project with FLASK" \
  --module src/flask.py \
  --tests tests/test_flask.py \
  --coverage "at least 80 percent"
```

```bash
cca --repo output/demo_streamlit full \
  --desc "Create a project with Streamlit that shows a number is prime or not after taking an input" \
  --module src/app.py \
  --tests tests/test_app.py \
  --coverage "at least 80 percent"
```

---

## Outputs

* Generated source files under `src/`
* Generated tests under `tests/`
* Coverage and pytest results evaluated during execution
* Report artifacts written to the repository (location configurable)

---

## Configuration

Global flags available to all commands:

* `--repo`
* `--model`
* `--host`
* `--temperature`