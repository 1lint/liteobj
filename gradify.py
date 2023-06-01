

def gradify_closure(ldict, argmaps, func_kwargs={}):
    
    from types import FunctionType
    for k, v in ldict.items():
        if isinstance(v, FunctionType):
            func = ldict.pop(k)
            break

    globals().update(ldict)
    func_kwargs = dict(func_kwargs)

    def gradify_func(*args):
        
        try:
            for (arg, argmap) in zip(args, argmaps):

                postprocessing = argmap.get("postprocessing", None)
                if postprocessing:
                    arg = eval(postprocessing)(arg)
                    
                kw_label = argmap["label"]
                func_kwargs[kw_label] = arg

            return func(**func_kwargs)
        except Exception as e:
            import gradio as gr
            raise gr.Error(f"Error: {e}")

    return gradify_func

def exec_to_dict(source, target=None):

    ldict = {}
    exec(source, globals(), ldict)

    return ldict.get(target, None) if target else ldict