# Classroom CLI Agent (cca) – Ollama-based

Default model: `devstral-small-2:24b-cloud`

Override options:
- `--model <name>`
- `OLLAMA_MODEL` environment variable

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

The CLI separates concerns explicitly:

1. **Program creation**
   Writes or updates source code under `src/`.

2. **Test generation**
   Writes pytest files under `tests/`.

3. **Test execution and reporting**
   Runs pytest with coverage once and evaluates results.

4. **Commit and push**
   Explicit Git operations.

There is no implicit iteration and no built-in single-command pipeline.
End-to-end execution is achieved by composing commands.

---

## Command overview

### `create`

Generate or update a single Python source module from a natural-language description.

- Writes code under `src/`
- Overwrites the target module file
- Does not generate tests
- Does not run pytest
- Does not commit

```bash
cca --repo <repo> create \
  --desc "<natural language description>" \
  --module <path/to/module.py>
```

---

### `gen-tests`

Generate pytest tests for an existing module.

- Writes pytest files under `tests/`
- Uses the description and current module code
- Does not execute tests
- Does not check coverage
- Does not modify source code
- Does not commit

```bash
cca --repo <repo> gen-tests \
  --desc "<natural language description>" \
  --module <path/to/module.py> \
  --tests <path/to/test_file.py>
```

---

### `report`

Execute tests once and evaluate results.

- Runs pytest with coverage exactly once
- Produces a structured test report
- Optionally enforces coverage thresholds
- Does not modify source code or tests
- Does not commit

```bash
cca --repo <repo> report
```

Optional flags:
- `--fail-on-tests`
- `--fail-on-coverage "<percent>"`

---

### `commit`

Persist changes to version control.

- Runs `git add -A`
- Creates a commit
- Optionally pushes to remote
- Does not generate or execute code

```bash
cca --repo <repo> commit \
  --message "<commit message>" \
  --push
```

---

## End-to-end examples (single command)

### Calculator

```bash
cca --repo output/demo_repo create \
  --desc "A calculator with add, subtract, multiply, divide functions" \
  --module src/calculator.py && \
cca --repo output/demo_repo gen-tests \
  --desc "A calculator with add, subtract, multiply, divide functions" \
  --module src/calculator.py \
  --tests tests/test_calculator.py --overwrite && \
cca --repo output/demo_repo report \
  --fail-on-tests \
  --fail-on-coverage "95 percent" && \
cca --repo output/demo_repo commit \
  --message "Agent: add calculator program and tests" \
  --push
```

---

### Prime Number Checker

```bash
cca --repo output/demo_repo create \
  --desc "Create Prime Number Checker in Python" \
  --module src/prime_checker.py && \
cca --repo output/demo_repo gen-tests \
  --desc "Create Prime Number Checker in Python" \
  --module src/prime_checker.py \
  --tests tests/test_prime_checker.py --overwrite && \
cca --repo output/demo_repo report \
  --fail-on-tests \
  --fail-on-coverage "90 percent" && \
cca --repo output/demo_repo commit \
  --message "Agent: add prime checker and tests" \
  --push
```

---

### Flask Project

```bash
cca --repo output/demo_flask create \
  --desc "Create a minimal project with FLASK" \
  --module src/flask.py && \
cca --repo output/demo_flask gen-tests \
  --desc "Create a minimal project with FLASK" \
  --module src/flask.py \
  --tests tests/test_flask.py --overwrite && \
cca --repo output/demo_flask report \
  --fail-on-tests \
  --fail-on-coverage "80 percent"  && \
cca --repo output/demo_flask commit \
  --message "Agent: add flask project and tests" \
  --push
```

---

### Streamlit Project

```bash
cca --repo output/demo_streamlit create \
  --desc "Create a project with Streamlit that shows a number is prime or not after taking an input" \
  --module src/app.py && \
cca --repo output/demo_streamlit gen-tests \
  --desc "Create a project with Streamlit that shows a number is prime or not after taking an input" \
  --module src/app.py \
  --tests tests/test_app.py --overwrite && \
cca --repo output/demo_streamlit report \
  --fail-on-tests \
  --fail-on-coverage "80 percent" && \
cca --repo output/demo_streamlit commit \
  --message "Agent: add streamlit app and tests" \
  --push
```


### Flask Project 2

```bash
cca --repo output/demo_flask scaffold \
  --desc "Create a Flask project with routes, services, and templates" \
  --out-dir . && \
cca --repo output/demo_flask gen-tests \
  --desc "Create a Flask project with routes, services, and templates" \
  --module src/app.py \
  --tests tests/test_app.py && \
cca --repo output/demo_flask report \
  --fail-on-tests \
  --fail-on-coverage "60 percent" && \
cca --repo output/demo_flask commit \
  --message "Agent: scaffold Flask project with tests" \
  --push
```

---

## Help

If a command does not appear in `cca --help`, it does not exist.
Add `--verbose` to print logs after repo info.
