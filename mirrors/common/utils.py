#!/usr/bin/env python
# -*- coding: utf-8 -*-
import itertools
import operator


def get_all_subclasses(cls):
    all_subclasses = set()

    for subclass in cls.__subclasses__():
        all_subclasses.add(subclass)
        all_subclasses.update(get_all_subclasses(subclass))

def groupby_sorted_dict(items, attr):
    return itertools.groupby(
        sorted(items, key=operator.itemgetter(attr)),
        key=operator.itemgetter(attr),
    )
