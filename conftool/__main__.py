from conftool.model.data_format import DataFormatModel
from . import VERSION
from .model.config import ConfigModel
from .model.exception import ConfigException
from .form import questionnaire
from .form.format import print_warning, print_fail, print_ok
from .form.text import t_warning_missing_auth, t_warning_missing_account_id, \
                       t_warning_missing_license

import argparse
import os.path

TITLE = f"New Relic Salesforce Exporter Config Tool {VERSION}"
DESCRIPTION = f"{TITLE}. Create or check configuration files."

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('config_file', type=str, help='File path. Config YAML file to create or check.')
    parser.add_argument('-c', '--check', action='store_true', help='Check configuration.')
    args = parser.parse_args()

    print(f"{TITLE}\n")

    if args.check:
        check_config(args.config_file)
    else:
        create_config(args.config_file)

def create_config(config_file: str):
    print("Creating new config file...\n")

    if os.path.isfile(config_file):
        print("Error: Config file already exists.")
        exit(1)

    try:
        conf = questionnaire.run()
    except KeyboardInterrupt:
        print("\nAborted.")
        exit(1)
    
    conf_yml = conf.to_yaml()

    print_config(conf_yml)

    try:
        with open(config_file, "w+") as file:
            try:
                file.write(conf_yml)
                file.close()
            except (IOError, OSError):
                print("Error: Could not write to file.")
                exit(1)
    except (FileNotFoundError, PermissionError, OSError):
        print("Error: Could not open file.")
        exit(1)

    print_ok("Done.")
    print()

def check_config(config_file: str):
    print("Validating config file...\n")

    if not os.path.isfile(config_file):
        print("Error: Config file doesn't exist.")
        exit(1)
    
    try:
        config_yaml_str = read_file(config_file)
    except Exception as err:
        print("Error opening file:", err)
        exit(1)

    try:
        config_model = ConfigModel.from_yaml(config_yaml_str)
    except ConfigException as err:
        print_fail(str(err))
        print()
        exit(1)

    for index,i in enumerate(config_model.instances):
        if i.arguments.auth is None:
            print(f"At instance #{index + 1}:")
            print_warning(t_warning_missing_auth)
            print()

    if  config_model.newrelic.data_format == DataFormatModel.EVENTS and \
        config_model.newrelic.account_id is None:
        print_warning(t_warning_missing_account_id)

    if config_model.newrelic.license_key is None:
        print_warning(t_warning_missing_license)
    
    # Serialize model into YAML
    serialized_yaml = config_model.to_yaml()
    print_config(serialized_yaml)

    print_ok("Validation OK!")
    print()

def read_file(file_name: str) -> str:
    with open(file_name) as file:
        return file.read()
    
def print_config(conf):
    print('---- CONFIG FILE:\n')
    print(conf)
    print('----')
    print()

if __name__ == "__main__": main()