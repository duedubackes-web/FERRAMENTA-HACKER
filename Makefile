.PHONY: verify test summary
verify:
	python3 scripts/workbench.py verify
test:
	python3 -m unittest discover -s tests -v
summary:
	python3 scripts/workbench.py summary
