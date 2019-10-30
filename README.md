# KTHAIS website

:computer: Website and management system for KTHAIS

:raising_hand: Current maintainer: [@oriolclosa](https://github.com/oriolclosa)

## Project setup

Requirements: Python 3.6 or greater, virtualenv and pip.

- `git clone https://github.com/kthaisse/website && cd website`.
- `virtualenv env --python=python3`.
- `source ./env/bin/activate`.
- `pip install -r requirements.txt`.

Continue with only one of the following sections depending on the purpose of the deploy.

### Local server

- `python manage.py migrate`.
- `python manage.py loaddata initial`.
- `python manage.py createsuperuser`.
- `python manage.py runserver`.

## Environmental variables

- **SECRET_KEY**: Application secret (to generate one, run `os.urandom(24)`).
- **PROD_MODE**: Disable Django debug mode, should be `True` on production site.

## Contribution

Please, report any incidents or questions to webdev@kthack.com.

### Style guidelines

A specific coding style is desired to keep consistency, please use [Black](https://github.com/python/black) in all your commited files. Pull Requests are required to pass all tests including the Travis CI pipeline on the repository.

### Commit message

Write it as you want, you did the work, not me. However, "Fix wrong event status due to a missing if" will always be better than "Events fixed" (doesn't apply to first commits of the repository).
