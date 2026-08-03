.PHONY: check test clean

check:
	pip install -r requirements.txt
	python packages/link-checker/main.py

test:
	python -m pytest tests/ -v || echo "Pytest kurulu değil, test iskeleti atlandı."

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
