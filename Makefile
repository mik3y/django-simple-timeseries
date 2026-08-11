toc:
	doctoc --notitle --github README.md

# Regenerate docs/api.md from the public docstrings.
apidocs:
	python scripts/gen_api_docs.py

.PHONY: toc apidocs
