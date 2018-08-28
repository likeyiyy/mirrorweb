#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# code is far away from bugs with the god animal protect
# I love animals. They taste delicious.
#         ┌─┐       ┌─┐
#      ┌──┘ ┴───────┘ ┴──┐
#      │                 │
#      │       ───       │
#      │  ─┬┘       └┬─  │
#      │                 │
#      │       ─┴─       │
#      │                 │
#      └───┐         ┌───┘
#          │         │
#          │         │
#          │         │
#          │         └──────────────┐
#          │                        │
#          │      Gods Bless        ├─┐
#          │      Never Bugs        ┌─┘
#          │                        │
#          └─┐  ┐  ┌───────┬──┐  ┌──┘
#            │ ─┤ ─┤       │ ─┤ ─┤
#            └──┴──┘       └──┴──┘

import urllib.parse

def decode_uri(str):
    return urllib.parse.unquote(str)

def split_field(field_name, model=None, manager=None):
    """
    :return:
    (target_model, head, remain_field, is_reverse_fk)
    """
    from django.db import models
    idx = field_name.find('__')
    if idx < 0:
        return None, field_name, None, False
    fk_field_name = field_name[0:idx]
    remain_field = field_name[idx + 2:]
    if model is not None:
        fk_field = model._meta.get_field_by_name(fk_field_name, ignore=True)
        if fk_field and isinstance(fk_field, models.ForeignKey):
            return fk_field.to, fk_field_name, remain_field, False
        elif fk_field_name in model._meta.reverse_relations:
            reverse_fk_model = model._meta.reverse_relations[fk_field_name]
            return reverse_fk_model, fk_field_name, remain_field, True
    return None, field_name, None, False


def get_fields_fk_and_reversefk_info(field_names, model):
    reverse_fk_key_field_map = {}
    fk_patch_field_map = {}
    field_list = []

    def track_fk_patch_key(field, model):
        _, head, remain, is_reverse_fk = split_field(field, model)
        if _ and is_reverse_fk:
            reverse_fk_key_field_map.setdefault(head, set())
            reverse_fk_key_field_map[head].add(remain)
        elif _:
            fk_patch_field_map.setdefault(head, set())
            fk_patch_field_map[head].add(remain)
        else:
            field_list.append(field)

    for field_name in field_names:
        track_fk_patch_key(field_name, model)

    return field_list, fk_patch_field_map, reverse_fk_key_field_map
