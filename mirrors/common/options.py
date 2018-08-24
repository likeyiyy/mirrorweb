#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from django.db import models

def get_options(option_key):
    return _get_options({
        'type__in': option_key.split(','),
        'is_deleted': False,
    })


def _get_options(filter_condition):
    from mirrors.models import Options
    from mirrors.api import api
    query = Options.objects.filter(**filter_condition).order_by(
        ('isnull(t1.order)', ''),
        ('order', 'asc'),
    )
    options = api._registry[Options].serialize_query_simple(query=query)
    val_key = 'zh_CN'
    for each in options:
        each['value'] = each[val_key]
        each['__name__'] = each['value']
    return options

default_ret = {
    "orderable": True,
    "searchable": True,
}

def field_to_view_type(field, meta=None, options_map=None, default=None):
    if default is None:
        default = default_ret

    val_attrs = [
        'default_value',
        'help_text',
        'editable',
        'notexcelable',
        'notmasseditable',
        'facet_able',
        'built_in',
        'ext_data',
        'disable_export',
        'option_key',
        'ext_data',
    ]

    if field.built_in and meta and field.name in meta.built_in_fields_desc:
        field_desc = meta.built_in_fields_desc[field.name]
        for attr in val_attrs:
            if getattr(field_desc, attr, None) is None:
                setattr(field_desc, attr, getattr(field, attr))
    else:
        field_desc = field

    ret = {
        "type": re.sub(r"Field", "", field.__class__.__name__).lower(),
        "order_field": "",
        "search_field": "",
    }
    ret.update(default)
    for val_attr in val_attrs:
        ret[val_attr] = getattr(field_desc, val_attr, getattr(field, val_attr))

    if field.primary_key:
        ret['editable'] = False

    if field.option_key:
        if options_map and field.option_key in options_map:
            options = options_map.get(field.option_key)
        else:
            options = get_options(field.option_key)
        ret['meta_class'] = {"meta": "dropdown", "type_data": options}
        ret['type'] = "dropdown"
    if isinstance(field, models.ForeignKey):
        fk_model = field.to
        ret['meta_class'] = {
            "meta": "foreignkey",
            "type_data": fk_model.__name__.lower(),
        }
        ret['type'] = "foreignkey"
    if field.primary_key:
        pk_model = field.model
        ret['meta_class'] = {
            "meta": "primarykey",
            "type_data": pk_model.__name__.lower(),
        }
        ret['type'] = "primarykey"
    if field.view_type:
        ret['type'] = field.view_type
        if ret.get('meta_class'):
            ret['meta_class']['meta'] = field.view_type
        if field.view_type == 'rate':
            ret['meta_class'] = {'meta': 'rate', 'type_data': field.options}
    return ret


class FieldShowScene(object):
    List = 1
    Edit = 2
    Search = 4
    Detail = 8

    All = List | Edit | Search | Detail

    @classmethod
    def without(cls, scene):
        val = cls.All ^ scene
        return val
