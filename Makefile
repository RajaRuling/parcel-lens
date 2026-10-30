.PHONY: results test browser words verify
results:
	.venv/bin/python -m src.run_all

test:
	.venv/bin/python -m pytest tests

browser:
	.venv/bin/python -m src.check_browser

words:
	.venv/bin/python -m src.check_public

verify:
	.venv/bin/python -m src.verify_artifacts
