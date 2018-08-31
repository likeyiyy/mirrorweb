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
from werkzeug.datastructures import ImmutableMultiDict
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from mirrors.common.rest import RestfulApi, RestfulResource
from django.views.decorators.csrf import csrf_exempt
from mirrors.common.logger import logger
from mirrors.libs.utils.gql_related import parse_gql

api = RestfulApi()


class RawBaseResource(RestfulResource):
    def get_urls(self):
        return [
            ('/id_list', self.id_list),
            ('/add', self.add),
            ('/edit', self.edit),
            ('/simple_list_with_ids', self.simple_list_with_ids),
        ]
    
    def _process_paginate(self, query, request_args=None, unlimited=False):
        try:
            paginate_by = int(request_args.get('paginate_by')  or 10,)
        except:
            paginate_by = 10
        page = request_args.get('page')
        pq = Paginator(query, paginate_by)
        currentpage = page
        totalpages = pq.num_pages
        totalcount = pq.count
        query = pq.get_page(currentpage)
        return query, currentpage, totalpages, totalcount

    def _process_query(self, query, request_args=None):
        gql = request_args.get('gql') or ''
        if gql:
            query_node = parse_gql(gql, self.model, self._model_name)
            if query_node is not None:
                query = query.filter(query_node)
        else:
            query = self.model.objects.filter(**request_args)
        return query
    
    def _process_simple_list_with_ids(self, query, request_args, unlimited=False):
        query = self._process_query(query, request_args=request_args)
        
        if unlimited is None:
            unlimited = bool(request_args.get('unlimited'))
        query, currentpage, totalpages, totalcount = self._process_paginate(
            query,
            request_args=request_args,
            unlimited=unlimited,
        )
        result = {
            "result": self.serialize_query_simple(query),
            "currentpage": currentpage,
            "totalpages": int(totalpages),
            "totalcount": totalcount,
        }
        if 'debug_query_sql' in request_args:
            result['debug'] = {
                'all_sql': query.print_sql(False, False),
            }
        return result
        
    
    def _process_id_list(self, query, request_args, unlimited=False):
        query = self._process_query(query, request_args=request_args)
        
        if unlimited is None:
            unlimited = bool(request_args.get('unlimited'))
        query, currentpage, totalpages, totalcount = self._process_paginate(
            query,
            request_args=request_args,
            unlimited=unlimited,
        )
        result = {
            "ids": [_.id for _ in query],
            "currentpage": currentpage,
            "totalpages": int(totalpages),
            "totalcount": totalcount,
        }
        if 'debug_query_sql' in request_args:
            result['debug'] = {
                'all_sql': query.print_sql(False, False),
            }
        return result
    
    def _id_list(self, request_args, unlimited=False):
        query = self.model.objects.all()
        result = self._process_id_list(
            query,
            request_args,
            unlimited,
        )
        return result
    
    def id_list(self, request):
        request_args = request.GET.dict()
        result = self._id_list(request_args)
        return self.response(result)
    
    def _simple_list_with_ids(self, request_args, unlimited=False):
        query = self.model.objects.all()
        result = self._process_simple_list_with_ids(
            query,
            request_args,
            unlimited,
        )
        return result
    
    def simple_list_with_ids(self, request):
        request_args = request.GET.dict()
        result = self._simple_list_with_ids(request_args)
        logger.debug(result)
        return self.response(result)
    
    def _process_data(self, data):
        s_class = self.get_serializer()
        id = data.get('id')
        if id:
            self.model.objects.filter(id=id).update(**data)
            return {'status': True, 'data': id}
        else:
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
        if not data.get('id'):
            return {'status': False, 'message': 'In Edit Mode, You Must Input Id'}
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
