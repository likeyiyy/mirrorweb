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

import warnings
import re
from rest_framework import serializers
from rest_framework.parsers import JSONParser
from django.urls import path
from django.http import JsonResponse
from mirrors.common.logger import logger

def slugify(s):
    return re.sub('[^a-z0-9_\-]+', '-', s.lower())


class RestfulResource(object):
    def __init__(self, rest_api, model):
        self.api = rest_api
        self.model = model
        self.allowed_methods = [
            'GET',
            'POST',
            'PUT',
            'DELETE',
        ]
    
    def get_serializer(self, fields=None):
        if not fields:
            fields = [_.name for _ in self.model._meta.fields]
        model_serializer_meta = type('Meta', (object,), {'model': self.model, 'fields': fields})
        model_serializer = type('{0}Serializer'.format(self.model.__name__), (serializers.ModelSerializer,), {
            'Meta': model_serializer_meta
        })
        return model_serializer
    
    def get_api_name(self):
        if not self.model:
            return '__base__'
        return slugify(self.model.__name__)
    
    def serialize_object(self, obj, fields=None):
        s = self.get_serializer(fields)
        return s(obj).data

    def serialize_query_simple(self, query, fields=None):
        s = self.get_serializer(fields)
        return s(query, many=True).data
    
    def getdata(self, request):
        if request.method == 'POST':
            return JSONParser().parse(request)
        raise Exception('Only Support POST method.')
    
    def response(self, data):
        return JsonResponse(data, safe=False)
    
    def operationresponse(self, data, status=True, extra=None):
        result = {'status': status}
        if status:
            result['data'] = data
        else:
            result['message'] = data
        if extra:
            result.update(extra)
        return self.response(result)
        

class RegistryProxy(dict):
    pass


class RestfulApi(object):
    
    def __init__(self):
        self._registry = RegistryProxy()
    
    @property
    def registry(self):
        return self._registry

    def register(self, model, provider=RestfulResource):
        if model in self._registry.keys():
            logger.warning(provider, self._registry[model])
            warnings.warn('Duplicate model registry: {}'.format(model))
        self._registry[model] = provider(self, model)

    def configure_routes(self):
        registers = []
        for model, provider in self._registry.items():
            if not model:
                continue
            api_name = provider.get_api_name()
            urls = provider.get_urls()
            for url, callback in urls:
                full_url = '/{0}{1}'.format(api_name, url)
                restful_url = 'rest{0}'.format(full_url)
                router = path(restful_url, callback, name=full_url)
                registers.append(router)
        return registers
        
    def setup(self):
        return self.configure_routes()
