init:
	pip install -r requirements/development.txt

release:
	# Options are "pypi" and "pypitest"
	python setup.py sdist upload -r $(environment)
