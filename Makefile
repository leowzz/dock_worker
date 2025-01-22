clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

build: clean
	python -m build

publish: build
	python -m twine upload dist/*

publish-test: build
	python3 -m twine upload --repository testpypi --repository-url https://test.pypi.org/legacy/ dist/*
