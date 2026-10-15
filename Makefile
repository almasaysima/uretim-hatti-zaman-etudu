.PHONY: install demo test lint docker-demo clean

install:
	pip install -r requirements-dev.txt

demo:            ## Sentetik veriyle çalıştır ve görsel raporu tarayıcıda aç
	python run_analysis.py --demo --open

test:
	python -m pytest

lint:
	ruff check .

docker-demo:     ## Docker ile demo (çıktılar ./outputs altında)
	docker build -t zaman-etudu .
	docker run --rm -v "$(PWD)/outputs:/app/outputs" zaman-etudu --demo

clean:
	rm -rf outputs __pycache__ .pytest_cache .ruff_cache
