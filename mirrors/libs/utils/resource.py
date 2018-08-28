#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import importlib
import traceback

def base_safe_import(package, client_name, *path):
    if package == 'custom_package':
        model_name = path[-1]
        try:
            importlib.import_module('.custom_package', 'mirrors')
            importlib.import_module('.{0}'.format(client_name), 'mirrors.custom_package')
            importlib.import_module('.{0}'.format(path[:-1]), 'mirrors.custom_package.{0}'.format(client_name))
        except:
            return None
        full_path = [package, client_name] + list(path[:-1])
        package = ".".join(full_path)
        try:
            import ipdb; ipdb.set_trace()
            return importlib.import_module(".{}".format(model_name), package)
        except ImportError as ex:
            if isinstance(ex.message, str) and model_name not in ex.message:
                traceback.print_exc()
            return None


def safe_import(
        model_name,
        package_name,
        client_name,
        package="custom_package",
):
    return base_safe_import(package, client_name, *[package_name, model_name])


