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

from django.db import models
from functools import lru_cache
from mirrors.common.utils import stringify

def _get_model_children(model, parent_id):
    from mirrors.common.utils import groupby_sorted
    result = []
    query = model.select(['id', 'parent_id'])
    ids_map = {
        key: map(lambda x: x.id, group)
        for key, group in groupby_sorted(query, 'parent_id')
    }

    def getchildren(parent_id):
        result.append(parent_id)
        children_ids = ids_map.get(parent_id, [])
        for id in children_ids:
            getchildren(id)

    getchildren(int(parent_id))
    return result


def _get_model_parents(model, id):
    result = []

    def getparents(id):
        result.append(id)
        parent = model.select().where(id=id)
        for item in parent:
            getparents(item.parent_id)

    getparents(id)
    if result.count(None):
        result.remove(None)

    return result


@lru_cache()
def get_model_children(model, parent_id):
    return _get_model_children(model, parent_id)


@lru_cache()
def get_model_parents(model, parent_id):
    return _get_model_parents(model, parent_id)


class InheritanceMixin(object):
    IS_ALL = True

    @property
    def children(self):
        model = type(self)
        return get_model_children(model, self.id)

    @property
    def parents(self):
        model = type(self)
        return get_model_parents(model, self.id)

    @property
    def full_path(self):
        parents = self.parents
        result = {}
        for item in type(self).select().where(id__in=parents):
            result[item.id] = item

        full_path = []
        parents.reverse()
        for _ in parents:
            name = getattr(result[_], 'name', None) or getattr(
                result[_],
                'zh_CN',
                None,
            )
            if name:
                full_path.append(name)
        return ' - '.join(full_path)

    @property
    def stringify_children(self):
        return stringify(self.children)

    @property
    def stringify_parents(self):
        return stringify(self.parents)

    @property
    def is_bottom(self):
        children = self.children
        if len(children) == 1 and children[0] == self.id:
            return True
        return False

    @property
    def is_top(self):
        parents = self.parents
        if len(parents) == 1 and parents[0] == self.id:
            return True
        return False


# Create your models here.

class Team(models.Model):
    name = models.CharField(max_length=200, null=True)
    

class BaseUser(models.Model):
    email = models.CharField(max_length=200)
    mobile = models.CharField(max_length=64)
    uid = models.CharField(max_length=200)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, default='', related_name='helloworld')
    
    def __str__(self):
        return self.email
    

class User(models.Model):
    baseuser =models.OneToOneField(BaseUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    
    def __str__(self):
        return self.name
    
    
class CustomFieldData(models.Model):
    external_type = models.CharField(max_length=64)
    external_id = models.IntegerField()
    field_name = models.CharField(max_length=64)
    value = models.TextField()
    
    def __str__(self):
        return '{0}-{1}-{2}'.format(self.external_type, self.external_id, self.field_name)


class CustomFieldMetaData(models.Model):
    external_type = models.CharField(max_length=64)
    external_id = models.IntegerField()
    field_name = models.CharField(max_length=64)
    type = models.CharField(max_length=64)
    view_type = models.CharField(max_length=64)
    # 各种able能力

    def __str__(self):
        return '{0}-{1}-{2}'.format(self.external_type, self.external_id, self.field_name)


class Options(models.Model):
    type = models.CharField(max_length=128)
    code = models.CharField(max_length=100)
    en_US = models.CharField(max_length=1000, null=True),
    zh_CN = models.CharField(max_length=1000, null=True),
    zh_TW = models.CharField(max_length=1000, null=True),
    color = models.CharField(max_length=50, null=True),
    is_buildin = models.BooleanField()
    ext = models.TextField(null=True)
    not_orderable = models.BooleanField(null=True)
    poset_order = models.IntegerField(null=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = (("type", "code"),)


model_map = {}


def load_model_map():
    from mirrors.common import utils
    global model_map

    for klass in utils.get_all_subclasses(models.Model):
        model_map[klass.__name__] = klass
        model_map[klass._meta.model_name.lower()] = klass
        model_map[klass._meta.db_table] = klass


def get_model_by_name(model_name):
    if not model_name:
        return
    if model_name in model_map:
        return model_map.get(model_name)
