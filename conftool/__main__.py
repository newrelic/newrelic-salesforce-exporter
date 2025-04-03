from . import VERSION
from .model.config import ConfigModel
from .model.exception import ConfigException
from .form import run_form

import argparse
import os.path

def main():
    parser = argparse.ArgumentParser(description=f'New Relic Salesforce Exporter Config Tool {VERSION}')
    parser.add_argument('config_file', type=str, help='Config YAML file path to load or create')
    parser.add_argument('-n', '--new', action='store_true', help='Create new configuration')
    args = parser.parse_args()

    if args.new and os.path.isfile(args.config_file):
        print("Error: Config file already exists.")
        exit(1)

    print(f"New Relic Salesforce Exporter Config Tool v{VERSION}\n")

    if args.new:
            run_form()
    else:
        #TODO: show file structure and allow editing
        
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
            print("------------------------------------ ERROR -------------------------------------")
            print(err)
            print("---------------------------------- TRACEBACK -----------------------------------")
            import traceback
            traceback.print_exc()
            print("--------------------------------------------------------------------------------")
            exit(1)
        
        pretty_print_config(config_model)


def read_file(file_name: str) -> str:
    with open(file_name) as file:
        return file.read()

def pretty_print_config(config_model: ConfigModel):
    import yaml
    def yaml_equivalent_of_default(dumper, data):
        dict_representation = data.__dict__
        node = dumper.represent_dict(dict_representation)
        return node
    yaml.add_representer(ConfigModel, yaml_equivalent_of_default)
    print(yaml.dump(config_model))

if __name__ == "__main__": main()