
clean:
	@echo "Clean the python virtualenv, distribution and package folders/files."
	rm -rf .venv build dist *.egg-info


clean-py:
	@echo "Clean the byte-compiled, optimized or DLL files."
	find . -name __pycache__ | xargs -i rm -rf {}
	find . -name '*.py[cod]' | xargs -i rm -rf {}


clean-all: clean clean-py
	@echo "Clean all."
	rm -rf ./static/


define INFOTEXT
---
A Python virtual environment has been created. You can activate it using:
  $$ source .venv/bin/activate

Once inside the virtual environment you will need to install the package using:
  $$ pip install -r requirements.txt

To exit out of the virtual environment just call the `deactivate` function:
  $$ deactivate

Once inside the virtual environment make sure to check the README.md file.
endef
export INFOTEXT

prepare: clean
	@echo "Creating a python3 virtual environment..."
	@virtualenv -p python3 .venv/
	@echo "Creating default settings file."
	@cp hoover/settings/{example_,}local.py
	@echo "$$INFOTEXT"

prepare-py2: clean
	@echo "Creating a python2 virtual environment..."
	@virtualenv -p python2 .venv/
	@echo "Creating default settings file."
	@cp hoover/settings/{example_,}local.py
	@echo "$$INFOTEXT"
