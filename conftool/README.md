# ConfTool

Configuration tool for the New Relic Salesforce Exporter.

## Requirements

Tested with Python versions 3.9 and 3.13.

## Install

From `conftool` folder:

- Create a virtual environment ([venv](https://virtualenv.pypa.io/en/latest/installation.html) is required):

    ```
    python<version> -m venv my_env
    ```

- Activate the environment:

    ```
    source my_env/bin/activate
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