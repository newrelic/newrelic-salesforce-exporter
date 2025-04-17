from . import VERSION
from .model.config import ConfigModel
from .model.exception import ConfigException
from .form import questionnaire
from .form.format import print_warning, print_fail, print_ok
from .form.text import t_warning_missing_auth

import argparse
import os.path

def main():
    parser = argparse.ArgumentParser(description=f'New Relic Salesforce Exporter Config Tool {VERSION}.')
    parser.add_argument('config_file', type=str, help='File path. Config YAML file to check or create.')
    parser.add_argument('-n', '--new', action='store_true', help='Create new configuration.')
    args = parser.parse_args()

    print(f"New Relic Salesforce Exporter Config Tool v{VERSION}\n")

    if args.new:
        if os.path.isfile(args.config_file):
            print("Error: Config file already exists.")
            exit(1)

        print("Creating new config file...\n")

        try:
            conf = questionnaire.run()
        except KeyboardInterrupt:
            print("\nAborted.")
            exit(1)
        
        print("Final config model:\n")
        print(conf.to_yaml())

        #TODO: write YAML to file

    else:
        if not os.path.isfile(args.config_file):
            print("Error: Config file doesn't exist.")
            exit(1)

        print("Validating config file...\n")
        
        try:
            config_yaml_str = read_file(args.config_file)
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
        
        # Serialize model into YAML
        print('---- CONFIG FILE:\n')
        serialized_yaml = config_model.to_yaml()
        print(serialized_yaml)
        print('----')
        print()

        print_ok("Validation OK!")
        print()

def read_file(file_name: str) -> str:
    with open(file_name) as file:
        return file.read()

if __name__ == "__main__": main()