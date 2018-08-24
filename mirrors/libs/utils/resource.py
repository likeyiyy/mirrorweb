#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import importlib
import traceback

def base_safe_import(package, client_name, *path):
    from django.conf import settings
    if package == 'custom_package':
        client_code = settings.CLIENT_CONFIG.get('CLIENT_CODE').lower()
        _ = '{}/'.format(client_code)
        model_name = path[-1]
        full_path = [package, client_name] + list(path[:-1])

        package = ".".join(full_path)
    
        try:
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


