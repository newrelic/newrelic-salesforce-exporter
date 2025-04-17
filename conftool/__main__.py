from . import VERSION
from .model.config import ConfigModel
from .model.exception import ConfigException
from .form import questionnaire

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
            print("---- ERROR:")
            print(err)
            print("----")
            exit(1)

        #TODO: if auth data not present, print warning message "t_warning_missing_auth"
        
        # Serialize model into YAML
        serialized_yaml = config_model.to_yaml()
        print(serialized_yaml)
        print("\nValidation OK!")

def read_file(file_name: str) -> str:
    with open(file_name) as file:
        return file.read()

if __name__ == "__main__": main()