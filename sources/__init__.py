from os.path import dirname, basename, isfile, join
import glob

modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [
    basename(f)[:-3] for f in modules
    if isfile(f) and not f.endswith('__init__.py')
]

# __all__ = ['beijing', 'inputs']

# import imp
# import os

# def load_from_file(filepath):
#     class_inst = None
#     expected_class = 'MyClass'

#     mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])

#     if file_ext.lower() == '.py':
#         py_mod = imp.load_source(mod_name, filepath)

#     elif file_ext.lower() == '.pyc':
#         py_mod = imp.load_compiled(mod_name, filepath)

#     if hasattr(py_mod, expected_class):
#         class_inst = getattr(py_mod, expected_class)()

#     return class_inst

# import sys
# import importlib.util

# file_path = 'pluginX.py'
# module_name = 'pluginX'

# spec = importlib.util.spec_from_file_location(module_name, file_path)
# module = importlib.util.module_from_spec(spec)
# spec.loader.exec_module(module)

# # check if it's all there..
# def bla(mod):
#     print(dir(mod))
# bla(module)

# import pkgutil

# __path__ = pkgutil.extend_path(__path__, __name__)
# for importer, modname, ispkg in pkgutil.walk_packages(path=__path__, prefix=__name__+'.'):
#     __import__(modname)
