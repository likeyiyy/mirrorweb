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
