from importlib import import_module
from fire import Fire
from omegaconf import OmegaConf, DictConfig, ListConfig
from typing import Any
import sys
from time import time
from pathlib import Path

SUPER_CONFIG_KEY = 'super'
CLASS_STRING = 'class_string' 

KWARGS = 'kwargs'
ARGS = 'args'
METHOD_KEY = 'method'

METADATA_KEY = 'lite_metadata'

# recursively load config with superconfigs
def load_config(yaml_file: str|Path) -> DictConfig:

    config = OmegaConf.load(yaml_file)

    if SUPER_CONFIG_KEY in config:
        super_configs = []
        for super_config in config[SUPER_CONFIG_KEY]:
            super_configs.append(load_config(super_config))
        config = OmegaConf.unsafe_merge(*super_configs, config)
        
    return config

def process_param(param):
    
    if isinstance(param, ListConfig):
        output_list = []
        for element in param:
            element = process_param(element)
            output_list.append(element)
        return output_list
    else:
        param = instantiate(param) if hasattr(param, CLASS_STRING) else param
        return param


# recursively instantiate objects that have objects as parameters
def instantiate(config: OmegaConf) -> Any:

    class_string = config.get(CLASS_STRING, None)
    if class_string is None:
        raise ValueError(f"Cannot instantiate object without '{CLASS_STRING}' key")
    
    module_name, class_name = class_string.rsplit(".", 1)
    module = import_module(module_name)
    module_attribute = getattr(module, class_name)

    method_string = config.get(METHOD_KEY, "")
    if method_string is None:
        return module_attribute

    kwargs = {}
    if KWARGS in config:
        for k, v in config[KWARGS].items():
            kwargs[k] = process_param(v)
 
    args = []
    if ARGS in config:
        for item in config[ARGS]:
            args.append(process_param(item))

    if method_string == "":
        return module_attribute(*args, **kwargs)
    else:
        method = getattr(module_attribute, method_string)
        return method(*args, **kwargs)

# convenience method for running object from yaml
def lite(yaml_file: str|Path, method_string: str=None, *args, **kwargs) -> Any:

    yaml_file = Path(yaml_file)
    sys.path.append(str(Path.cwd()))
    sys.path.append(str(yaml_file.parent.resolve()))

    config = load_config(yaml_file)

    metadata = dict(config.get(METADATA_KEY, {}))
    metadata["config_path"] = str(Path(yaml_file).resolve())
    metadata["time"] = time()

    object = instantiate(config)
    # this bypasses setattr checks against assigning object attributes
    vars(object).update(metadata) 
    
    #config[METADATA_KEY] = metadata
    #OmegaConf.save(config=config, f=yaml_file)

    if method_string is None:
        return object
    
    # if method string is defined, run instantiated object method with args and kwargs
    try:
        method = getattr(object, method_string)
        return object, method(*args, **kwargs)
    except KeyboardInterrupt:
        return object, None

def main():
    return Fire(lite)

if __name__ == '__main__':
    main()