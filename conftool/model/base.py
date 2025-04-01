from typing_extensions import Self
from enum import Enum
import yaml

class BaseModel:
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
    def map_yaml(cls, this: Self, yaml_val: any) -> Self:
        if '__inner_val__' in cls.__annotations__:
            # It's a newtype base model, with a plain type inside.
            # Set the inner value.
            inner_val_type = cls.__annotations__['__inner_val__']
            if inner_val_type != type(yaml_val):
                raise Exception(f"Attribute must be of type `{inner_val_type.__name__}` and is a `{type(yaml_val).__name__}`")
            setattr(this, '__inner_val__', yaml_val)
        else:
            for attr_name, attr_class in cls.__annotations__.items():
                cls.map_attribute(this, attr_name, attr_class, yaml_val)
        this.check()
        return this

    @classmethod
    def map_attribute(cls, this: any, attr_name: str, attr_class: type, yaml_dic: dict):
        if is_base_model(attr_class):
            value = cls.map_base_model_attribute(attr_name, attr_class, yaml_dic)
        elif is_enum(attr_class):
            value = cls.map_enum_attribute(attr_name, attr_class, yaml_dic)
        elif is_list(attr_class):
            value = cls.map_list_attribute(attr_name, attr_class, yaml_dic)
        else: # is_just_a_plain_type
            default_instance = attr_class()
            value = yaml_dic.get(attr_name, default_instance)
            if type(value) != type(default_instance):
                raise Exception(f"Attribute `{attr_name}` must be of type `{attr_class.__name__}` and is a `{type(value).__name__}`")
            if type(default_instance) == dict:
                if len(attr_class.__args__) != 2:
                    raise Exception(f"Dict `{attr_name}` must be defined with two inner types (key and value)")
                key_type: type = attr_class.__args__[0]
                val_type: type = attr_class.__args__[1]
                for k,v in value.items():
                    if type(k) != key_type:
                        raise Exception(f"Dict key type must be `{key_type.__name__}` and is `{type(k).__name__}`")
                    if type(v) != val_type:
                        raise Exception(f"Dict key type must be `{val_type.__name__}` and is `{type(v).__name__}`")
        setattr(this, attr_name, value)

    @classmethod
    def map_base_model_attribute(cls, attr_name: str, attr_class: type[Self], yaml_dic: dict) -> any:
        subyaml = yaml_dic.get(attr_name)
        base_model_instance = attr_class()
        if subyaml is None:
            return base_model_instance
        else:
            return attr_class.map_yaml(base_model_instance, subyaml)
        
    @classmethod
    def map_list_attribute(cls, attr_name: str, attr_class: type[list[Self]], yaml_dic: dict) -> any:
        list_of_items: list = attr_class()
        subyaml_list = yaml_dic.get(attr_name)
        if subyaml_list is None:
            return []
        if type(subyaml_list) is not list:
            raise Exception(f"Object at YAML attribute `{attr_name}` must be a list")
        if len(attr_class.__args__) != 1:
            raise Exception(f"List `{attr_name}` must be defined with one inner type only")
        # Get type of list contents
        item_type: type[Self] = attr_class.__args__[0]
        for item in subyaml_list:
            list_item = item_type()
            # map "item" into "list_item"
            if is_base_model(item_type):
                item_type.map_yaml(list_item, item)
                list_of_items.append(list_item)
            else: # is_just_a_plain_type
                if item_type != type(item):
                    raise Exception(f"List `{attr_name}` must be of type `{item_type.__name__}` and is a `{type(item).__name__}`")
                list_of_items.append(item)
        return list_of_items
    
    @classmethod
    def map_enum_attribute(cls, attr_name: str, attr_class: type[Enum], yaml_dic: dict) -> any:
        attr_value = yaml_dic[attr_name]
        try:
            value = attr_class(attr_value)
        except Exception:
            raise Exception(f"Invalid value `{attr_value}`, `{attr_name}` must be one of the following: {[e.value for e in attr_class]}")
        return value
    
    # To be overwritten by subclasses. Check data integrity.
    # Should raise an exception if check fails.
    def check(self): pass

# Helpers

def is_enum(cls: type) -> bool:
    return issubclass(cls, Enum)

def is_base_model(cls: type) -> bool:
    return issubclass(cls, BaseModel)

def is_list(cls: type) -> bool:
    return type(cls()) is list