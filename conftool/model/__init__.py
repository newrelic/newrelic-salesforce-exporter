from .enum import ConfigEnum

# Convert config object into dctionary
def to_dict(obj, classkey=None) -> dict:
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            if v is not None:
                data[k] = to_dict(v, classkey)
        if not data:
            return None
        else:
            return data
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        ret_list = []
        for v in obj:
            if v is not None:
                sub_dat = to_dict(v, classkey)
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
                    sub_dat = to_dict(value, classkey)
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