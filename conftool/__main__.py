from . import VERSION
from .model.config import ConfigModel
from .model.exception import ConfigException
from .model.enum import ConfigEnum
from .form import questionnaire

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
            questionnaire.run()
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
        
        # Serialize model into YAML
        import yaml
        serialized_yaml = yaml.dump(todict(config_model), sort_keys=False)
        
        print(serialized_yaml)

        #TODO: write YAML to file

def read_file(file_name: str) -> str:
    with open(file_name) as file:
        return file.read()

def todict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            if v is not None:
                data[k] = todict(v, classkey)
        if not data:
            return None
        else:
            return data
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        ret_list = []
        for v in obj:
            if v is not None:
                sub_dat = todict(v, classkey)
                if sub_dat is not None:
                    ret_list.append(sub_dat)
        if not ret_list:
            return None
        else:
            return ret_list
    elif hasattr(obj, "__dict__"):
        if obj is None:
            return None
        data_dict = {}
        for key, value in obj.__dict__.items():
            if not callable(value) and not key.startswith('_'):
                if value is not None:
                    sub_dat = todict(value, classkey)
                    if sub_dat is not None:
                        data_dict[key] = sub_dat
            elif key == "__objclass__" and issubclass(value, ConfigEnum):
                # Enum
                return str(obj)
        if not data_dict:
            return None
        else:
            return data_dict
    else:
        return obj

if __name__ == "__main__": main()