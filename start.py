import os
from pprint import pprint
from models import *
from helpers import *
import sources


def loadModule(name):
    module = import_module(name)
    module_dict = module.__dict__

    try:
        to_import = module.__all__
    except AttributeError:
        to_import = [name for name in module_dict if not name.startswith('_')]
    globals().update({name: module_dict[name] for name in to_import})

    return module


def main():
    el = Link()
    print(el.title)
    all_sources = sources.__all__
    # Website level
    # for source in all_sources:
    #     module_name = 'sources.' + source
    #     target = import_module(module_name)
        
    #     target_dir = target.folder_name | source;
    #     target_urls = target.base_urls;
    #     target_level = '';
    #     target_category = '';
    #     target_url = '';
        
    #     # Parent level
    #     for level, urls in target_urls.items():
    #         target_level = level;
            
    #         # Category level
    #         for item in urls:
    #             target_category = item['category']
    #             print(item['url'])


main()