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

# Create your models here.

class BaseUser(models.Model):
    name = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    mobile = models.CharField(max_length=64)
    uid = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name
    

class User(models.Model):
    baseuser =models.OneToOneField(BaseUser, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.baseuser.name
    
    
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
