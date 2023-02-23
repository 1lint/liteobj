
import __main__
from inspect import getmembers, ismethod, getfile
import torch
import os
from pathlib import Path
from pytorch_lightning.tuner.tuning import Tuner
from shutil import copy
from liteobj.lite import CONFIG_PATH_KEY
from pytorch_lightning.loggers.tensorboard import TensorBoardLogger

class Lab():
    def __init__(self, 
        trainer, 
        model=None, 
        datamodule=None, 
        ckpt_path=None, 
        state_dict_path=None, 
        **info
    ):
        vars(self).update(locals())
        self.tuner = Tuner(trainer)

        if ckpt_path == 'auto':
            ckpt_paths = self.get_ckpt_paths()
            self.ckpt_path = None
            if len(ckpt_paths) > 0:
                self.ckpt_path = ckpt_paths[-1]
            print(f'Checkpoint path set to {self.ckpt_path}')

        if state_dict_path is not None:
            self.load_state_dicts(state_dict_path)

        self.core = dict([(key, getattr(self, key)) for key in ['model', 'datamodule', 'ckpt_path']])

    def lr_find(self, *args, **kwargs):
        return self.tuner.lr_find(model=self.model, datamodule=self.datamodule, *args, **kwargs)

    def scale_batch_size(self, *args, **kwargs):
        return self.tuner.scale_batch_size(model=self.model, datamodule=self.datamodule, *args, **kwargs)

    # save a copy of relevant source files from project directory into log folder
    def save_source(self):
        log_source_dir = Path(self.log_dir)/'source'
        os.makedirs(log_source_dir, exist_ok=True)
        source_paths = [f'Checkpoint source: {self.ckpt_path}']

        if CONFIG_PATH_KEY in vars(self).keys():
            source_path = Path(vars(self)[CONFIG_PATH_KEY]).absolute()
            copy(source_path, log_source_dir)
            source_paths.append(f'Config source: {source_path}')

        for object in [self.model, self.datamodule, self]:
            source_path = getfile(object.__class__)
            copy(source_path, log_source_dir)
            source_paths.append(f'{object.__class__.__name__} source: {source_path}')

        with open(log_source_dir/'source_paths.txt', 'w+') as f:
            f.write('\n'.join(source_paths))
        return source_paths

    # assumes tensorboard logger directory structure. To do: check if this is consistent with other pl loggers
    def get_ckpt_paths(self, log_dir=None):
        if log_dir is None:
            log_dir = Path(self.log_dir).parent
        else:
            log_dir = Path(log_dir)
        ckpt_paths = list(log_dir.glob('checkpoints/*.ckpt')) + list(log_dir.glob('*/checkpoints/*.ckpt'))
        return ckpt_paths

    # restore checkpoints for testing/debugging in jupyter notebook
    def restore_checkpoint(self, ckpt_path=None):
        if ckpt_path is None:
            ckpt_path = self.ckpt_path
        self.trainer.state.fn = 'jupyter_notebook'
        self.trainer.strategy.connect(self.model)
        self.trainer._callback_connector._attach_model_callbacks()
        self.trainer._callback_connector._attach_model_logging_functions()
        self.trainer._checkpoint_connector.restore(ckpt_path)


    def load_state_dicts(self, file_paths=None, target_module=None, strict=False):

        if file_paths == None:
            ckpt_paths = self.get_ckpt_paths()
            if len(ckpt_paths) > 0:
                file_paths = [ckpt_paths[-1]]
            else:
                print('No state dicts loaded')
                return
        elif isinstance(file_paths, str):
            file_paths = [file_paths]

        if target_module is None:
            target_module = self.model

        for file_path in file_paths:
            state_dict = torch.load(file_path, map_location='cpu')
            if 'state_dict' in state_dict:
                state_dict = state_dict['state_dict']
            target_module.load_state_dict(state_dict, strict=strict)
            print(f'loaded state dict from {file_path} to {target_module.__class__.__name__}')


    def save_state_dict(self, save_path=None, as_checkpoint=False):
        if save_path is None:
            save_path = Path(self.log_dir)/f'{self.model.__class__.__name__}.pt'
        if as_checkpoint:
            return self.trainer.save_checkpoint(save_path)
        return torch.save(self.model.state_dict(), save_path)


    def __repr__(self):
        #repr = super().__repr__() + '\n'
        repr = ''
        for k, v in self.info.items():
            repr += f'{k}: {str(v)}\n'
        for k, v in self.core.items():
            repr += f'{k}: {v.__class__.__name__}\n'
        return repr


    def fit(self, *args, **kwargs):
        self.save_source()
        return self.trainer.fit(*args, **kwargs, **self.core)

    def validate(self, *args, **kwargs):
        self.save_source()
        return self.trainer.validate(*args, **kwargs, **self.core)

    def test(self, *args, **kwargs):
        self.save_source()
        return self.trainer.test(*args, **kwargs, **self.core)

    def predict(self, *args, **kwargs):
        self.save_source()
        return self.trainer.predict(*args, **kwargs, **self.core)

    # get batch from datamodule
    def get_batch(self, batch_idx=0):
        self.datamodule.prepare_data()
        try: self.datamodule.setup(stage='fit')
        except: pass
        batch_iters = iter(self.datamodule.train_dataloader())

        for _ in range(batch_idx):
            next(batch_iters)
        return next(batch_iters)

    # for easier attribute/variable access in jupyter notebook
    def unload(self, _to=__main__):
        vars(_to).update(vars(self))
        methods = getmembers(self, predicate=ismethod)

        for method_name, method in methods:
            setattr(_to, method_name, method)

    # reattach modified attributes/variables to self for further testing
    def reload(self, _from=__main__):
        vars(self).update({key: var for key, var in vars(_from).items() if key in vars(self)})
        methods = getmembers(_from, predicate=ismethod)

        for method_name, method in methods:
            if hasattr(self, method_name) and callable(getattr(self, method_name)):
                setattr(self, method_name, method)

    # same as trainer.log_dir but skip the strategy broadcast step
    # needed to access log_dir before trainer is intialized for multidevice strategy
    @property
    def log_dir(self):
        if len(self.trainer.loggers) > 0:
            if not isinstance(self.trainer.loggers[0], TensorBoardLogger):
                dirpath = self.trainer.loggers[0].save_dir
            else:
                dirpath = self.trainer.loggers[0].log_dir
        else:
            dirpath = self.trainer.default_root_dir
        return dirpath

