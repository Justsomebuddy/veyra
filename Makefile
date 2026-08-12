SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

PYTHON ?= python3
PROJECT_PYTHONPATH ?= .
PYTEST ?= $(PYTHON) -m pytest
SAGE ?= sage
CARGO ?= $(shell command -v cargo 2>/dev/null || printf '%s' "$(HOME)/.cargo/bin/cargo")
RUSTFMT_CARGO ?= $(CARGO) +1.95.0
RUST_TEST_CARGO ?= $(CARGO) +1.95.0
LEAN_JOBS ?= 8
ACTIVE_IGNORE ?=

.PHONY: help status lint test cert sage-smoke sage-required sage-doctest rust lean package-smoke portable hygiene diff-check verify omegaa-collect tables notebooks

help:
	@printf '%s\n' \
	  'Veyra command runner' \
	  '' \
	  'Core verification:' \
	  '  make test          Run the public pytest suite' \
	  '  make cert          Run executable Veyra certificate suite' \
	  '  make sage-smoke    Run Sage facade smoke checks' \
	  '  make sage-required Run the facade through real SageMath' \
	  '  make sage-doctest  Run veyra_sage doctests' \
	  '  make rust          Run locked native formatting/tests' \
	  '  make lean          Compile all 47 pinned Lean sources' \
	  '  make package-smoke Build/install/inspect wheel and sdist' \
	  '  make portable      Run the shell-neutral portable lane' \
	  '  make hygiene       Check active file line hygiene' \
	  '  make diff-check    Check patch whitespace integrity' \
	  '  make verify        Run the complete Linux source lane' \
	  '' \
	  'Experimental (not part of make verify):' \
	  '  make omegaa-collect  Collect isolated Omega-A tests without running them' \
	  '' \
	  'Artifacts:' \
	  '  make tables        Regenerate processed table artifacts' \
	  '  make notebooks     Regenerate Sage-lab notebook artifacts' \
	  '' \
	  'Inspection:' \
	  '  make status        Show git branch/status'

status:
	@echo '[1/1] Git working-tree status'
	@git status --short --branch

lint:
	@echo '[1/1] Running Ruff'
	@$(PYTHON) -m ruff check src veyra_sage vam scripts tests

test:
	@echo '[1/1] Running public pytest suite'
	@PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTEST) -q $(ACTIVE_IGNORE)

cert:
	@echo '[1/1] Running executable certificate suite'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTHON) scripts/certify_veyra.py

sage-smoke:
	@echo '[1/1] Running Sage facade smoke checks'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTHON) scripts/sage_smoke.py

sage-required:
	@echo '[1/1] Running facade checks through real SageMath'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(SAGE) -python scripts/sage_smoke.py --require-sage

sage-doctest:
	@echo '[1/1] Running veyra_sage doctests'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(SAGE) -python scripts/sage_doctest.py

rust:
	@echo '[1/2] Checking native Rust formatting'
	@$(RUSTFMT_CARGO) --version | grep -q '^cargo 1\.95\.0 '
	@cd vam/native && $(RUSTFMT_CARGO) fmt --all -- --check
	@echo '[2/2] Running locked native Rust tests'
	@cd vam/native && $(RUST_TEST_CARGO) test --locked

lean:
	@echo '[1/1] Compiling the complete pinned Lean source graph'
	@$(PYTHON) scripts/check_lean_sources.py --jobs $(LEAN_JOBS)

package-smoke:
	@echo '[1/1] Building and inspecting Python distributions'
	@$(PYTHON) scripts/package_smoke.py

portable:
	@echo '[1/1] Running portable source/package verification'
	@$(PYTHON) scripts/verify_portable.py

hygiene:
	@echo '[1/1] Running portable repository hygiene'
	@$(PYTHON) scripts/project_hygiene.py

diff-check:
	@echo '[1/3] Checking working-tree whitespace integrity'
	@git diff --check
	@echo '[2/3] Checking staged whitespace integrity'
	@git diff --cached --check
	@echo '[3/3] Checking current commit whitespace integrity'
	@git show --check --format= HEAD

omegaa-collect:
	@echo '[1/1] Collecting isolated Omega-A tests (experimental; not stable verification)'
	@cd experimental/omegaa && PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. $(PYTEST) -p no:cacheprovider --collect-only -q tests

verify:
	@echo '[1/11] Ruff'
	@$(MAKE) --no-print-directory lint
	@echo '[2/11] Pytest'
	@$(MAKE) --no-print-directory test
	@echo '[3/11] Certificates'
	@$(MAKE) --no-print-directory cert
	@echo '[4/11] Real Sage smoke'
	@$(MAKE) --no-print-directory sage-required
	@echo '[5/11] Sage doctest'
	@$(MAKE) --no-print-directory sage-doctest
	@echo '[6/11] Rust'
	@$(MAKE) --no-print-directory rust
	@echo '[7/11] Lean'
	@$(MAKE) --no-print-directory lean
	@echo '[8/11] Package smoke'
	@$(MAKE) --no-print-directory package-smoke
	@echo '[9/11] Portable lane'
	@$(MAKE) --no-print-directory portable
	@echo '[10/11] Hygiene'
	@$(MAKE) --no-print-directory hygiene
	@echo '[11/11] Diff check'
	@$(MAKE) --no-print-directory diff-check
	@echo '[done] Veyra verification complete'

tables:
	@echo '[1/1] Regenerating processed table artifacts'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTHON) scripts/generate_tables.py

notebooks:
	@echo '[1/1] Regenerating Sage-lab notebook artifacts'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTHON) scripts/generate_notebooks.py
