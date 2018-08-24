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

api = RestfulApi()


class RawBaseResource(RestfulResource):
    def get_urls(self):
        return [
            ('/id_list', self.id_list),
            ('/simple_list_with_ids', self.simple_list_with_ids),
        ]
    
    def id_list(self, request):
        query = self.model.objects.all()
        result = self.serialize_query_simple(query)
        return self.response(result)
    
    def simple_list_with_ids(self, request):
        pass


api.register(None, RawBaseResource)
