# ckanext-dwr-theme

Theme and template customizations for CKAN 2.10.

What's included:

| Feature | Where |
|---|---|
| Template overrides (`base.html`, `footer.html`) | `ckanext/dwr_theme/templates/` |
| CSS / JS via webassets (`dwr-theme/dwr-theme-css`, `dwr-theme/dwr-theme-js`) | `ckanext/dwr_theme/assets/` |
| Static files (served from `/`) | `ckanext/dwr_theme/public/` |
| Template helpers: `h.dwr_theme_greeting()`, `h.dwr_theme_dataset_count()`, `h.dwr_theme_show_dataset_count()` | `ckanext/dwr_theme/helpers.py` |
| Flask blueprint: page at `/dwr-theme` (endpoint `dwr_theme.index`) | `ckanext/dwr_theme/views.py` |
| API action `dwr_theme_hello` + auth function + validator `dwr_theme_no_digits` | `ckanext/dwr_theme/logic/` |
| CLI: `ckan dwr-theme hello [NAME]` | `ckanext/dwr_theme/cli.py` |
| Declared config options | `ckanext/dwr_theme/config_declaration.yaml` |
| Tests (pytest-ckan) + GitHub Actions CI | `ckanext/dwr_theme/tests/`, `.github/workflows/test.yml` |

## Requirements

| CKAN version | Compatible? |
|---|---|
| 2.9 and earlier | no |
| 2.10 | yes |
| 2.11 | should work (not tested) |

Python 3.8+.

## Installation

1. Activate your CKAN virtualenv:

        . /usr/lib/ckan/default/bin/activate

2. Copy or clone this extension into your CKAN `src` directory and install it:

        cd /usr/lib/ckan/default/src
        git clone https://github.com/your-org/ckanext-dwr-theme.git
        cd ckanext-dwr-theme
        pip install -e .
        pip install -r requirements.txt

3. Add `dwr-theme` to `ckan.plugins` in your CKAN config file
   (by default `/etc/ckan/default/ckan.ini`). Put it **before** other plugins
   whose templates you want this extension to override:

        ckan.plugins = dwr-theme activity datastore ...

4. Restart CKAN, e.g. on Ubuntu with supervisor/uWSGI:

        sudo supervisorctl restart ckan-uwsgi:*

5. Visit `http://<your-ckan>/dwr-theme` and try the API:

        curl "http://<your-ckan>/api/3/action/dwr_theme_hello?name=CKAN"
        ckan -c /etc/ckan/default/ckan.ini dwr-theme hello CKAN

### With ckan-docker

Put this folder in `src/` of your [ckan-docker](https://github.com/ckan/ckan-docker)
checkout (dev mode installs everything in `src/` automatically), then add
`dwr-theme` to `CKAN__PLUGINS` in `.env` and run `docker compose -f docker-compose.dev.yml up --build`.

## Config settings

    # Greeting prefix used by the dwr_theme_hello action (default: Hello)
    ckanext.dwr_theme.greeting = Sawasdee

    # Show the dataset count on /dwr-theme (default: true)
    ckanext.dwr_theme.show_dataset_count = true

List all declared options with:

    ckan -c /etc/ckan/default/ckan.ini config declaration dwr-theme

## Development

    git clone https://github.com/your-org/ckanext-dwr-theme.git
    cd ckanext-dwr-theme
    pip install -e .
    pip install -r dev-requirements.txt

## Tests

`test.ini` expects CKAN's source to be a sibling directory (`../ckan/test-core.ini`);
adjust the `use = config:` line if yours lives elsewhere. Then:

    ckan -c test.ini db init
    pytest --ckan-ini=test.ini ckanext/dwr_theme

## Translations

    python setup.py extract_messages
    python setup.py init_catalog -l th
    python setup.py compile_catalog

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
