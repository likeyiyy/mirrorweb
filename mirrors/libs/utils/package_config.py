#!/usr/bin/env python
# -*- coding: utf-8 -*-

children_map = {
    "base": [
        "business",
        "customer"
    ],
    "business": [
        "test1",
    ],
    "customer": [
        "test2",
    ],
}


def default_target_company(target_company):
    if target_company:
        return target_company
    return "business"


def build_parent_map():
    parent_map = {}
    for parent, children in children_map.items():
        for child in children:
            parent_map[child] = parent
    return parent_map


parent_map = build_parent_map()


def build_module_path(t, reverse=True):
    t = default_target_company(t)
    module_path = [t]
    while parent_map.get(t):
        parent = parent_map.get(t)
        module_path.append(parent)
        t = parent
    if reverse:
        module_path.reverse()
    return module_path
