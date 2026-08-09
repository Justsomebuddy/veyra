SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

PYTHON ?= python3
PROJECT_PYTHONPATH ?= .
PYTEST ?= $(PYTHON) -m pytest
ACTIVE_IGNORE ?=
.PHONY: help status python-check test cert sage-smoke sage-doctest hygiene verify omegaa-collect tables notebooks

help:
	@printf '%s\n' \
	  'Veyra command runner' \
	  '' \
	  'Core verification:' \
	  '  make test          Run the public pytest suite' \
	  '  make cert          Run executable Veyra certificate suite' \
	  '  make sage-smoke    Run Sage facade smoke checks' \
	  '  make sage-doctest  Run veyra_sage doctests' \
	  '  make hygiene       Check repository cache-ignore hygiene' \
	  '  make verify        Run test + cert + Sage + hygiene' \
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
	@printf '%s\n' \
	  '' \
	  'Override PYTHON=... to select the interpreter (3.11 or newer).'

status:
	@echo '[1/1] Git working-tree status'
	@git status --short --branch

python-check:
	@$(PYTHON) -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 11) else 1)' || { \
		printf '%s\n' \
			"veyra needs CPython 3.11 or newer ($(PYTHON) is older)." \
			"Use: PYTHON=python3.11 make <target>" >&2; \
		exit 1; \
	}

test: python-check
	@echo '[1/1] Running public pytest suite'
	@PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTEST) -q $(ACTIVE_IGNORE)

cert: python-check
	@echo '[1/1] Running executable certificate suite'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTHON) scripts/certify_veyra.py

sage-smoke:
	@echo '[1/1] Running Sage facade smoke checks'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTHON) scripts/sage_smoke.py

sage-doctest:
	@echo '[1/1] Running veyra_sage doctests'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTHON) scripts/sage_doctest.py

hygiene:
	@echo '[1/1] Checking Python cache files remain ignored'
	@git check-ignore -q .pytest_cache/ && git check-ignore -q src/core/__pycache__/ && echo '[ok] cache ignore rules active'

omegaa-collect:
	@echo '[1/1] Collecting isolated Omega-A tests (experimental; not stable verification)'
	@cd experimental/omegaa && PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. $(PYTEST) -p no:cacheprovider --collect-only -q tests

verify:
	@echo '[1/5] Pytest'
	@$(MAKE) --no-print-directory test
	@echo '[2/5] Certificates'
	@$(MAKE) --no-print-directory cert
	@echo '[3/5] Sage smoke'
	@$(MAKE) --no-print-directory sage-smoke
	@echo '[4/5] Sage doctest'
	@$(MAKE) --no-print-directory sage-doctest
	@echo '[5/5] Hygiene'
	@$(MAKE) --no-print-directory hygiene
	@echo '[done] Veyra verification complete'

tables:
	@echo '[1/1] Regenerating processed table artifacts'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTHON) scripts/generate_tables.py

notebooks:
	@echo '[1/1] Regenerating Sage-lab notebook artifacts'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTHON) scripts/generate_notebooks.py
