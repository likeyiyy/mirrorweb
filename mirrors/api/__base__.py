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
from mirrors.common.rest import RestfulApi, RestfulResource
from django.views.decorators.csrf import csrf_exempt


api = RestfulApi()


class RawBaseResource(RestfulResource):
    def get_urls(self):
        return [
            ('/id_list', self.id_list),
            ('/add', self.add),
            ('/edit', self.edit),
            ('/simple_list_with_ids', self.simple_list_with_ids),
        ]
    
    def id_list(self, request):
        query = self.model.objects.all()
        query_result = self.serialize_query_simple(query, fields=['id'])
        ids = [_.get('id') for _ in query_result]
        return self.response({
            'ids': ids
        })
    
    def simple_list_with_ids(self, request):
        pass
    
    def _process_data(self, data):
        s_class = self.get_serializer()
        serializer = s_class(data=data)
        if serializer.is_valid():
            ins = serializer.save()
            return {'status': True, 'data': ins.id}
        return {'status': False, 'message': serializer.errors}

    def _add(self, data):
        if data.get('id'):
            return {'status': False, 'message': 'In Add Mode, You Can Not Input Id'}
        result = self._process_data(data)
        return result
        
    def _edit(self, data):
        if data.get('id'):
            return {'status': False, 'message': 'In Add Mode, You Must Input Id'}
        result = self._process_data(data)
        return result
    
    @csrf_exempt
    def add(self, request):
        data = self.getdata(request)
        result = self._add(data)
        return self.response(result)
    
    @csrf_exempt
    def edit(self, request):
        data = self.getdata(request)
        result = self._edit(data)
        return self.response(result)
    
    
api.register(None, RawBaseResource)
