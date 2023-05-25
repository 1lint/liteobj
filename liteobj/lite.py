from importlib import import_module
from fire import Fire
from omegaconf import OmegaConf, DictConfig
from typing import Any
import sys
import os
from time import time
from pathlib import Path

SUPER_CONFIG_KEY = 'super'
CLASS_STRING = 'class_string' 

KWARGS = 'kwargs'
ARGS = 'args'
METHOD_KEY = 'method'

METADATA_KEY = 'lite_metadata'


# compile function source and assign object to target_name
def compile_callable(source, target_name=None):

    ldict = {}
    exec(source, globals(), ldict)

    if target_name:
        return ldict[target_name]
    else:
        for v in ldict.values():
            if callable(v):
                return v

# pack args and kwargs into a list
def listify(*args, **kwargs):
    return [*args, *kwargs.values()]

# computes class_string for class object
def get_class_string(_class):
    return f'{_class.__module__}.{_class.__name__}'

# recursively load config with superconfigs
def load_config(yaml_file: str) -> DictConfig:

    config = OmegaConf.load(yaml_file)

    if SUPER_CONFIG_KEY in config:
        super_configs = []
        for super_config in config[SUPER_CONFIG_KEY]:
            super_configs.append(load_config(super_config))
        config = OmegaConf.unsafe_merge(*super_configs, config)
        
    return config

# recursively instantiate objects that have objects as parameters
def instantiate(config: OmegaConf) -> Any:

    class_string = config.get(CLASS_STRING, None)
    if class_string is None:
        raise ValueError(f"Cannot instantiate object without '{CLASS_STRING}' key")
    
    module_name, class_name = class_string.rsplit(".", 1)
    module = import_module(module_name)
    module_class = getattr(module, class_name)

    kwargs = {}
    if KWARGS in config:
        for k, v in config[KWARGS].items():
            kwargs[k] = instantiate(v) if isinstance(config[KWARGS][k], DictConfig) else v
 
    args = []
    if ARGS in config:
        for item in config[ARGS]:
            args.append(instantiate(item)) if isinstance(item, DictConfig) else args.append(item)


    # allow custom instantiation method
    method_string = config.get(METHOD_KEY, '__init__')
    if method_string is None:
        return module_class

    # have to invoke __init__ method as special case due to nuances of python compiler
    if method_string == '__init__':
        return module_class(*args, **kwargs)
    else:
        method = getattr(module_class, method_string)
        return method(*args, **kwargs)

# convenience method for running object from yaml
def run(yaml_file: str, method_string: str=None, *args, **kwargs) -> Any:
    sys.path.append(os.getcwd()) 

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
    return Fire(run)

if __name__ == '__main__':
    main()