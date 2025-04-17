from . import VERSION
from .model.config import ConfigModel
from .model.exception import ConfigException
from .form import questionnaire
from .form.format import print_warning, print_fail, print_ok
from .form.text import t_warning_missing_auth

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

    if not args.check:
        print("Creating new config file...\n")

        if os.path.isfile(args.config_file):
            print("Error: Config file already exists.")
            exit(1)

        try:
            conf = questionnaire.run()
        except KeyboardInterrupt:
            print("\nAborted.")
            exit(1)
        
        print_config(conf.to_yaml())

        #TODO: write YAML to file

        print_ok("Done.")
        print()
    else:
        print("Validating config file...\n")

        if not os.path.isfile(args.config_file):
            print("Error: Config file doesn't exist.")
            exit(1)
        
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