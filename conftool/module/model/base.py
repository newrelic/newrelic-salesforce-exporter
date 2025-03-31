from typing_extensions import Self
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
    
    @classmethod
    def map_yaml(cls, this: Self, yaml_dic: dict) -> Self:
        # For each attribute of class get value from YAML,
        # or default value if attr doesn't exist in the YAML.
        for attr, attr_class in cls.__annotations__.items():
            if issubclass(attr_class, BaseModel):
                subyaml = yaml_dic.get(attr)
                instance = attr_class()
                if subyaml is None:
                    value = instance
                else:
                    value = attr_class.map_yaml(instance, subyaml)
            else:
                value = yaml_dic.get(attr, attr_class())
            setattr(this, attr, value)
        return this