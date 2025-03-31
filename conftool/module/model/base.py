from typing_extensions import Self
from enum import Enum
import yaml

class BaseModel():
    @classmethod
    def from_yaml(cls, yaml_str: str) -> Self:
        # Parse YAML
        parsed_yaml: dict = yaml.safe_load(yaml_str)
        # Create instance this class
        this = cls()
        # Map YAML into class instance
        return cls.map_yaml(this, parsed_yaml)
    
    # For each attribute of class get value from YAML
    @classmethod
    def map_yaml(cls, this: Self, yaml_dic: dict) -> Self:
        for attr_name, attr_class in cls.__annotations__.items():
            cls.map_attribute(this, attr_name, attr_class, yaml_dic)
        this.check()
        return this

    @classmethod
    def map_attribute(cls, this: any, attr_name: str, attr_class: type, yaml_dic: dict):
        if issubclass(attr_class, BaseModel):
            value = cls.map_base_class_attribute(attr_name, attr_class, yaml_dic)
        else:
            if issubclass(attr_class, Enum):
                attr_value = yaml_dic[attr_name]
                value = attr_class(attr_value)
            else:
                instance = attr_class()
                if isinstance(instance, list):
                    value = cls.map_list_attribute(instance, attr_name, attr_class, yaml_dic)
                else:
                    value = yaml_dic.get(attr_name, instance)
        setattr(this, attr_name, value)

    @classmethod
    def map_base_class_attribute(cls, attr_name: str, attr_class: type[Self], yaml_dic: dict) -> any:
        subyaml = yaml_dic.get(attr_name)
        instance = attr_class()
        if subyaml is None:
            return instance
        else:
            return attr_class.map_yaml(instance, subyaml)
        
    @classmethod
    def map_list_attribute(cls, instance: list, attr_name: str, attr_class: type[list[Self]], yaml_dic: dict) -> any:
        subyaml_list = yaml_dic.get(attr_name)
        if subyaml_list is None:
            return []
        if not isinstance(subyaml_list, list):
            raise Exception(f"Object at YAML attribute `{attr_name}` must be a list")
        # Get first type of list content (assuming we have only one type)
        list_item_type: type[Self] = attr_class.__args__[0]
        for item in subyaml_list:
            list_item = list_item_type()
            # map "item" into "list_item"
            if issubclass(list_item_type, BaseModel):
                list_item_type.map_yaml(list_item, item)
                instance.append(list_item)
            else:
                instance.append(item)
        return instance
    
    # To be overwritten by subclasses. Check data integrity.
    # Should raise an exception if check fails.
    def check(self):
        pass