# Diablo

Diablo supports UC Berkeley's Course Capture service.

![Picture of sun setting in the city of Hatra, Iraq](src/assets/iraqi-sunset-from-exorcist-movie.png)

## Installation

* Install Python 3
* Create your virtual environment (venv)
* Install dependencies

```
pip3 install -r requirements.txt [--upgrade]
```

### Front-end dependencies

```
npm install
```

### Create Postgres user and databases

```
createuser diablo --no-createdb --no-superuser --no-createrole --pwprompt
createdb diablo --owner=diablo
createdb diablo_test --owner=diablo
createdb diablo_loch_test --owner=diablo

# Load schema
export FLASK_APP=run.py
flask initdb
```

### Create local configurations

If you plan to use any resources outside localhost, put your configurations in a separately encrypted area:

```
mkdir /Volumes/XYZ/diablo_config
export DIABLO_LOCAL_CONFIGS=/Volumes/XYZ/diablo_config
```

## Run tests, lint the code

We use [Tox](https://tox.readthedocs.io) for continuous integration. Under the hood, you'll find [PyTest](https://docs.pytest.org), [Flake8](http://flake8.pycqa.org) and [ESLint](https://eslint.org/). Please install NPM dependencies (see above) before running tests.
```
# Run all tests and linters
tox

# Pytest
tox -e test

# Run specific test(s)
tox -e test -- tests/test_models/test_foo.py
tox -e test -- tests/test_externals/

# Linters, à la carte
tox -e lint-py
tox -e lint-vue

# Auto-fix linting errors in Vue code
tox -e lint-vue-fix

# Lint specific file(s)
tox -e lint-py -- scripts/foo.py
```
