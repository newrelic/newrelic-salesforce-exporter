# ConfTool

Configuration tool for the New Relic Salesforce Exporter.

## Requirements

Python 3.9.

TODO: Test with newer versions of Python.

## Install

From `conftool` folder:

- Create a virtual environment (how to install [venv](https://virtualenv.pypa.io/en/latest/installation.html)):

    ```
    python<version> -m venv sf_env
    source sf_env/bin/activate
    ```

- Then install dependencies:

    ```
    pip install -r requirements.txt
    ```

## Usage

From repo's root folder.

1. To create new config file:

    ```
    python -m conftool path/to/config.yml
    ```

1. To validate an existing config file:

    ```
    python -m conftool path/to/config.yml --check
    ```