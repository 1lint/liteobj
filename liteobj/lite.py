from importlib import import_module, reload
from fire import Fire
from omegaconf import OmegaConf, DictConfig
from typing import Any
import sys
import os

# originally inspired by object instantiation code found in https://github.com/CompVis/taming-transformers. 
# added logic to recursively instantiate objects used as parameters, and recursively load omegaconfigs from yaml files to support superconfigs

SUPER_CONFIG_KEY = 'super'

OBJECT_PARAM_KEY = 'object_params'
CLASS_NAME_KEY = 'target' 
PARAM_KEY = 'params'
METHOD_KEY = 'method'

CONFIG_PATH_KEY = '_source_config_path'


# load omegaconfig from string filepath to yaml file
# if omegaconfig has SUPER_CONFIG_KEY key, recursively load omegaconfigs from corresponding value, which should be list of yaml filepaths to superconfigs
def load_config(yaml_file: str) -> DictConfig:

    config = OmegaConf.load(yaml_file)

    if SUPER_CONFIG_KEY in config:
        super_configs = []
        for super_config in config[SUPER_CONFIG_KEY]:
            super_configs.append(load_config(super_config))
        config = OmegaConf.unsafe_merge(*super_configs, config)
        
    return config


# instantiate object(s) specified by omegaconfig 
# if omegaconfig contains OBJECT_PARAM_KEY key, recursively instantiate objects from corresponding value, which should also be an omegaconfig
def instantiate_from_config(config: OmegaConf) -> Any:

    object_params = {}
    if OBJECT_PARAM_KEY in config:
        for object_name, object_config in config[OBJECT_PARAM_KEY].items():
            object_params[object_name] = instantiate_from_config(object_config)

    module_string, class_string = config[CLASS_NAME_KEY].rsplit(".", 1)
    if module_string in sys.modules:
        module = reload(sys.modules[module_string])
    else:
        module = import_module(module_string)
    module_class = getattr(module, class_string)

    # allow instantiation options like huggingface from_pretrained, instead of standard __init__
    # method should not use super(), see https://stackoverflow.com/questions/12047847/super-object-not-calling-getattr
    method_string = config.get(METHOD_KEY, '__init__') 
    if method_string is None:
        return module_class
    elif method_string == '__init__':
        return module_class(**config.get(PARAM_KEY, dict()), **object_params)
    method = getattr(module_class, method_string)
    return method(**config.get(PARAM_KEY, dict()), **object_params)

# instantiate object from yaml file, then run object method specified in method_string. 
# convenience function to run pytorch-lightning trainer methods from terminal
# i.e. to train, run "">> python lite.py path/to/omegaconfig.yaml fit"
def run(yaml_file: str, method_string: str=None, *args, **kwargs) -> Any:

    # add current directory to path for importing local modules
    sys.path.append(os.getcwd()) 

    config = load_config(yaml_file)
    object = instantiate_from_config(config)

    # attach source config path to object, avoid invoking unpredictable __setattr__ logic
    vars(object).update({CONFIG_PATH_KEY: yaml_file}) 
    
    if method_string is None:
        return object
    try:
        method = getattr(object, method_string)
        return object, method(*args, **kwargs)
    except KeyboardInterrupt:
        return object, None

def main():
    return Fire(run)

if __name__ == '__main__':
    main()