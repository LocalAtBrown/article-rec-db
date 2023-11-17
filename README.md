_This branch houses the effort to move our DB code to a SQLAlchemy-based stack and is under active development in parallel with the move to Google Analytics 4. For the current production code, see the `main` branch._

# article-rec-db

<!-- [![Release](https://img.shields.io/github/v/release/LocalAtBrown/article-rec-db)](https://img.shields.io/github/v/release/LocalAtBrown/article-rec-db) -->
<!-- [![Build status](https://img.shields.io/github/workflow/status/LocalAtBrown/article-rec-db/merge-to-main)](https://img.shields.io/github/workflow/status/LocalAtBrown/article-rec-db/merge-to-main) -->

[![Python version](https://img.shields.io/badge/python_version-3.9-blue)](https://github.com/psf/black)
[![Code style with black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/psf/black)
[![More style with flake8](https://img.shields.io/badge/code_style-flake8-blue)](https://flake8.pycqa.org)
[![Imports with isort](https://img.shields.io/badge/%20imports-isort-blue)](https://pycqa.github.io/isort/)
[![Type checking with mypy](https://img.shields.io/badge/type_checker-mypy-blue)](https://mypy.readthedocs.io)
[![License](https://img.shields.io/github/license/LocalAtBrown/article-rec-db)](https://img.shields.io/github/license/LocalAtBrown/article-rec-db)

Database models and migrations for the Local News Lab's article recommendation system.

## Usage

A note before continuing: A lot of the commands you'll see below are wrapped inside [Poe tasks](https://poethepoet.natn.io/index.html) defined in `pyproject.toml`. Poe is installed as a dev-dependency; run `poe --help` to get a list of tasks and their descriptions. It's entirely possible to run commands without using Poe, but if you decide to use Poe, make sure to read through the tasks to understand what they do.

### As a package

We use [SQLModel](https://sqlmodel.tiangolo.com/), a layer on top of SQLAlchemy with Pydantic, to define our tables.
This is useful because we can import this package to interact with the tables AND have Pydantic objects in Python
that correspond to a row in the table.

To install the package from PyPi, run: `pip install article-rec-db`. Check existing versions
[here](https://pypi.org/project/article-rec-db/).

### Database management

We use [Terraform](https://developer.hashicorp.com/terraform) to manage cluster entities such as databases, roles and extensions. The code is in the `terraform` directory. Stages (dev and prod) are represented as different databases. To make changes to an existing database,

1. Make changes inside `terraform/modules`.
2. Run `poe terraform [stage] plan` to see the changes that will be applied to the corresponding database.
3. At this point, if you're happy, you can run `poe terraform [stage] apply` yourself, but we prefer a CI/CD approach. Merging a PR to the `dev` branch will trigger a plan to be applied to the `dev` database, and the same for the `prod` branch. _We always merge to `dev` first, then do another merge from `dev` to `prod`._

### Table and column migrations

So you made some changes to what tables there are, what columns there are, indices, etc. and you'd like to
update the databases. This is what alembic is for! (And notice the difference between Terraform and alembic: Terraform manages database entities that are not specific to a database, like roles and extensions, while alembic manages database entities that are specific to a database, like tables and columns.)

To generate a new revision after you've updated the models:

1. Run this from the root of the project: `DB_CONNECTION_STRING='postgresql://user:password@host:port/db_name' alembic revision --autogenerate -m "message"`. (There's a Poe task for this: run `poe rmtdiff -d db_name -m "message"`)
2. Check the `/alembic/versions/` directory for the new revision and verify that it does what you want it to. Run `TYPE=alembic poe test` to test models against a local DB initialized via Alembic, and resolve issues as needed.
3. Run this from the root of the project: `DB_CONNECTION_STRING='postgresql://user:password@host:port/db_name' alembic upgrade head`. Note that you only need to generate the revision file (step 1) _once_ because we want the same content in each environment's database, but you do need to run the `upgrade head` command once _for each_ database (change the DB_NAME to the desired target). (There's a Poe task for this: run `poe rmtupgrade -d db_name`)

Similar to database management, we let our CI/CD handle Step 3.

_Note to LNL devs: Our automated deployment process will run the Terraform changes first, then the Alembic changes. So, for example, using Terraform to create a new database and Alembic to create a new table in that database will work in just one PR, but creating a new table with Alembic and using Terraform to grant a role access to that table won't. Best to divide changes into atomic units, each handled by a single PR._

## Development

This project uses [Poetry](https://python-poetry.org/) to manage dependencies. It also helps with pinning dependency and python
versions. We also use [pre-commit](https://pre-commit.com/) with hooks for [isort](https://pycqa.github.io/isort/),
[black](https://github.com/psf/black), and [flake8](https://flake8.pycqa.org/en/latest/) for consistent code style and
readability. Note that this means code that doesn't meet the rules will fail to commit until it is fixed.

We use [mypy](https://mypy.readthedocs.io/en/stable/index.html) for static type checking. This can be run [manually](#run-static-type-checking),
and the CI runs it on PRs to the `main` branch. We also use [pytest](https://docs.pytest.org/en/7.2.x/) to run our tests.
This can be run [manually](#run-tests) and the CI runs it on PRs to the `main` branch.

### Setup

1. [Install Poetry](https://python-poetry.org/docs/#installation).
2. Run `poetry install --no-root`
3. Run `source $(poetry env list --full-path)/bin/activate && pre-commit install && deactivate` to set up `pre-commit`

You're all set up! Your local environment should include all dependencies, including dev dependencies like `black`.
This is done with Poetry via the `poetry.lock` file.

### Run Code Format and Linting

`pre-commit run --all-files` runs isort, black, and flake8 all in one go, and is also run on every commit.

`poe format` does what `pre-commit run --all-files` does and also formats the Terraform code.

### Run Static Type Checking

To manually run mypy, simply run `mypy` from the root directory of the project. It will use the default configuration
specified in `pyproject.toml`.

### Update Dependencies

To update dependencies in your local environment, make changes to the `pyproject.toml` file then run `poetry update` from the root directory of the project.

To update Terraform dependencies, make changes to `versions.tf` files as necessary.

### Run Tests

To manually run rests, you need to have a Postgres instance running locally on port 5432. One way to do this
is to run a Docker container, then run the tests while it is active.

1. (If you don't already have the image locally) Run `docker pull ankane/pgvector:v<version used in your remote db>`
2. Run `docker run --rm --name postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_HOST_AUTH_METHOD=trust -p 127.0.0.1:5432:5432/tcp postgres`
3. Run `pytest tests` from the root directory of the project. Explore the `pytest` docs (linked above)

Note that if you decide to run the Postgres container with different credentials (a different password, port, etc.) or
via a different method, you will likely need to update the test file to point to the correct Postgres instance.

Additionally, if you want to re-run the tests, you want to make sure you start over from a fresh Postgres
instance. If you run Postgres via Docker, you can simply `ctrl-C` to stop the image and start a new one.

Steps 2 and 3 can be combined into one Poe task: `poe test`, which also stops the container after the tests are done, even if tests fail. In addition, you can also run `poe lclstart` to just start the container, and `poe lclstop` to stop it whenever you're done. `poe lclconnect` will connect you to the container via `psql` so you can poke around.

`poe test`, by default, is equivalent to `TYPE=sqlmodel poe test`, which tests the models against a local DB initialized via SQLModel. You can also run `TYPE=alembic poe test` to test the models against a local DB initialized via Alembic. The first is more convenient and is good for development, the second reflects the production environment more closely and is good for testing Alembic revisions once you're about to submit a PR.
