# Liteobj


<a href="https://github.com/1lint/liteobj/blob/master/LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/License-MIT-yellowgreen" /></a>

Liteobj is a convenience tool for configuring large objects in Python.
ML experiments often involve instantiating multiple layers of nested objects, leading to cumbersome instantiation logic and configuration file formats specific to each project's code. Through some recursion, liteobj enables a simplified object configuration format can be more directly compiled into the specified object. 

Please see [tutorial.ipynb](https://github.com/1lint/liteobj/blob/master/tutorial.ipynb) for an explanation and demonstration of `liteobj`. 

## Install

Install from pip
```
pip install liteobj
```

As a basic example, run the Pytorch Lightning Basic GAN tutorial from https://pytorch-lightning.readthedocs.io/en/stable/notebooks/lightning_examples/basic-gan.html
```
git clone https://github.com/1lint/liteobj
cd liteobj
python -m pip install -r requirements.txt
python lite.py lab.yaml fit
```

To run lite.py in other directories, install the pip package. Then run configurations with the `lite` console script 
```
python -m pip install .
lite configs/lab.yaml fit
```

Syntax is 
```
lite {config_path} {object_method}
```
Where `config_path` is path to the yaml file to instantiate, and `object_method` is the name of the object method to invoke once the object is instantiated. 








