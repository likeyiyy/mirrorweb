#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mirrors.libs.custom_loader.custom_loader_base import LoaderService, CustomRegister


class CustomQueryFilterManager(object):
    ANY_FILTER = "____any____"

    def __init__(self):
        self.query_map = {}

    def add_query(self, model, name, request_attr, fn):
        self.query_map.setdefault(model, [])

        def default_get_attr(request_args):
            if name == self.ANY_FILTER:
                return request_args
            else:
                return request_args.get(name)

        if callable(request_attr):
            get_attr_fn = request_attr
        else:
            get_attr_fn = default_get_attr

        self.query_map[model].append({
            "name": name,
            "get_attr_fn": get_attr_fn,
            "func": fn
        })

    def filter_query(self, model, query, query_args):
        query_filter_list = self.query_map.get(model, [])
        for query_filter in query_filter_list:
            get_attr_fn = query_filter["get_attr_fn"]
            func = query_filter["func"]
            args = get_attr_fn(query_args)
            if args:
                query = func(query, args)
        return query


class CustomQueryFilterService(LoaderService):
    manager_cls = CustomQueryFilterManager


custom_query_filter_service = CustomQueryFilterService()


class QueryRegister(CustomRegister):
    service_ins = custom_query_filter_service

    def __call__(self, name, request_attr=None):
        def decorator(fn):
            self.manager.add_query(model=self.model_name,
                                   name=name,
                                   request_attr=request_attr,
                                   fn=fn)
            return fn

        return decorator
