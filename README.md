# Liteobj

Liteweight configuration format for defining and recursively instantiating python objects composed of nested object parameters

## Install

Install from pip
```
pip install liteobj
```

## Quickstart Example with Gradio App
```
git clone https://github.com/1lint/liteobj
cd liteobj
pip install liteobj==0.0.5 gradio==3.32.0
lite demo.yaml launch --server_port=7860 --server_name=0.0.0.0
```
CLI syntax is 
```
lite {config_path} {object_method} {method_args} {method_kwargs}
```

`config_path` is path to the yaml file to instantiate, and is the only required parameter. Returns the instantiated object instance
`object_method` is the name of the object method to invoke once the object is instantiated. If passed, returns the output of the object method
`method_args` and `method_kwargs` are passed directly into the object method. 

Example use as python library 
```python
from liteobj import lite
demo = lite("demo.yaml")
demo.launch(server_port=7860, server_name="0.0.0.0")
```


## Tutorial
(tutorial currently out of date, to be updated)
See [tutorial.ipynb](https://github.com/1lint/liteobj/blob/master/tutorial.ipynb) for example use of `liteobj` to quickly run training with pytorch-lightning







