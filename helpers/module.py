import os


def import_module(name):
    mod = __import__(name)
    for s in name.split('.')[1:]:
        mod = getattr(mod, s)

    return mod