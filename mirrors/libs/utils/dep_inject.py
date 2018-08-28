import inspect


def always_none():
    while True:
        yield None


def func_call_kwargs(fn, _kwargs):
    arg_spect = inspect.getargspec(fn)
    if inspect.ismethod(fn):
        arg_names = arg_spect[0][1:]
    else:
        arg_names = arg_spect[0]
    default_value = arg_spect[3] or always_none()
    _args = {}
    for arg_name, default_value in zip(arg_names, default_value):
        _args[arg_name] = _kwargs.get(arg_name, default_value)

    return fn(**_args)
