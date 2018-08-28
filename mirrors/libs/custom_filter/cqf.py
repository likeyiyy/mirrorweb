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
from functools import reduce

from mirrors.models import get_model_by_name
from mirrors.libs.custom_loader.custom_loader_base import LoaderService, CustomRegister, BaseLoader, \
    BaseModelManager
from mirrors.libs.utils import func_call_kwargs, TrackerDict, split_field
import inspect
from collections import OrderedDict
from mirrors.common.logger import logger

ANY_FILTER = "____any____"


def get_all_args(request_args):
    return request_args


class ModelQueryFilterManager(BaseModelManager):
    def __init__(self, model_name=None):
        super(ModelQueryFilterManager, self).__init__(model_name)
        self.ignore_fields = set()
        self.exclude = set()
        self.query_filters = OrderedDict()
        self._rn = "qr"
        self.filter_operator_map = {}
        self._single_level_fk = set()
        self._registered_query_operators = {}
        self._fake_query_operators = {}


    def add_query(self, name, fn, operator):
        if operator:
            key = "{}__{}".format(name, operator)
            self._registered_query_operators.setdefault(name, ['eq'])
            self._registered_query_operators[name].append(operator)
        else:
            key = name
        self.query_filters[key] = fn
        if name not in self.registered_key:
            self.registered_key.append(name)
            
    def get_registered_operators(self):
        reg_operators = self._registered_query_operators.values()
        fake_operators = self._fake_query_operators.values()
        operators = list(reg_operators) + list(fake_operators)
        if operators:
            return set(reduce(lambda x, y: x + y, operators))
        return set()

    def filter_query(self, query, query_args):
        for key, value in query_args.iteritems():
            func = self.query_filters.get(key) \
                   or self.query_filters.get(key.replace('__eq', ''))
            if func:
                if self.model:
                    query = query.switch(self.model)
                query = func(query, value)
        return query

    def add_exclude(self, exclude):
        self.exclude.update(exclude)

    def get_exclude(self):
        return tuple(self.exclude)

    def add_ignore_fields(self, ignore_fields):
        self.ignore_fields.update(ignore_fields)

    def get_ignore_fields(self):
        return tuple(self.ignore_fields)

    def add_single_level_fk(self, fk_list):
        self._single_level_fk.update(fk_list)

    def get_view_data_list(self):
        lst = super(ModelQueryFilterManager, self).get_view_data_list()
        lst = self.patch_filter_operator(lst)

        def add_not_to_load(obj):
            name = obj['name']
            if name in self._single_level_fk:
                obj['type']['not_load'] = True
            return obj
        return map(add_not_to_load, lst)

    def _inheritance_fk_to_comtree(self, field):
        ret = {
            'meta_class': {
                "meta": "comtree",
                "type_data": field.to.__name__.lower()
            },
            'type': "comtree"
        }
        return ret

    def get_query_filters_names(self):
        return self.registered_key

    def is_valid_operator(self, name, operator):
        operators = self._registered_query_operators.get(name, ['eq'])
        if operator in operators:
            return True
        return False

    def patch_filter_operator(self, lst):
        def add_operator(each):
            name = each['name']
            each.setdefault('type', {})
            each['type']['operators'] = self.get_operator(name, each['type'])
            return each

        return map(add_operator, lst)

    def get_valid_lookup_operator(self):
        return reduce(lambda x, y: set(x) | set(y), self._registered_query_operators.values() or ['eq'])

    def get_operator(self, name, type_data):
        if name in self.filter_operator_map:
            return self.filter_operator_map[name]
        if name in self.registered_key:
            return self._registered_query_operators.get(name) or ['']
        model, _, remain_field, _ = split_field(name, self.model)
        if model:
            model_manager = custom_query_filter_service.manager.get_model_manager(model)
            return model_manager.get_operator(remain_field, type_data)

        if 'type' not in type_data:
            raise AttributeError("{}:{} not register filter operator".format(self.model_name, name))
        operators = self.get_type_operator(type_data['type'], type_data)
        return operators

    def get_type_operator(self, type, type_data=None):
        if type in ['radio', 'checkboxdropdown']:
            options = type_data['meta_class']['type_data']
            if len(options) and options[0].get('not_orderable'):
                return ['eq', 'isnull']
            else:
                return ['eq', 'ne', 'gt', 'lt', 'isnull']
        if type in ['checkbox']:
            return ['eq', 'ne', 'isnull']
        elif type == 'primarykey':
            return ['eq', 'ne']
        elif type == 'comtree':
            return ["children", "eq", "ne", "isnull"]
        elif type in ["foreignkey", 'foreign_key']:
            return ["eq", "ne", "isnull"]
        elif type in ["integer", 'numeric', 'decimal', 'int', 'double']:
            return ['range', 'eq', 'ne', 'lt', 'lte', 'gt', 'gte', 'isnull']
        elif type in ['char', 'text', 'multiline']:
            return ['icontains', 'eq', 'isnull']
        elif type in ['bool', 'boolean']:
            return ['eq', 'isnull']
        elif type in ['date', 'datetime']:
            return ['range', 'eq', 'lt', 'gt', 'gte', 'lte', 'today', 'yesterday', 'this_week',
                    'last_week', 'this_month', 'last_month', 'this_quarter', 'last_quarter',
                    'next_quarter', 'this_year', 'last_year',
                    'three_days_ago', 'gte_days_ago', 'one_week_ago', 'two_weeks_ago', 'one_month_ago', 'three_months_ago',
                    'six_months_ago', 'one_year_ago', 'in_one_year', 'until_today',
                    'until_this_week', 'until_this_month', 'isnull']
        elif type in ['dropdown']:
            return ['s', 'isnull']
        elif type in ['reverse_foreignkey']:
            return ["s", "isnull"]
        else:
            logger.warning('Unknow type to get operator:{}'.format(type))
            return ['eq']


class ModelQueryFilterManagerAdapter(ModelQueryFilterManager):
    def __init__(self, model_name=None):
        super(ModelQueryFilterManagerAdapter, self).__init__(model_name)

    operator = 'inheritance'

    def patch_operator(self, ret, name, type_data):
        return ret

    def get_operator(self, name, type_data):
        ret = super(ModelQueryFilterManagerAdapter, self).get_operator(name, type_data)
        return self.patch_operator(ret, name, type_data)


class QueryRegister(CustomRegister):
    def __call__(self, name, view_type=None, show=True, operator=None):

        def decorator(fn):
            self.model_manager.add_query(name=name, fn=fn, operator=operator)
            return fn

        if view_type is not None:
            if not isinstance(view_type, list):
                view_type = [{name: view_type}]
            for obj in view_type:
                self.model_manager.add_view_type(*obj.popitem())
        if not show and name != ANY_FILTER:
            self.model_manager.add_never_show_key(name)
        return decorator


class CustomQueryFilterManager(BaseLoader):
    ModelManagerCls = ModelQueryFilterManagerAdapter
    RegCls = QueryRegister
    dir_path = "custom_filter"

    def __init__(self, host=None):
        super(CustomQueryFilterManager, self).__init__(host)
        self.empty_query_filter = ModelQueryFilterManager()


class CustomQueryFilterService(LoaderService):
    manager_cls = CustomQueryFilterManager


custom_query_filter_service = CustomQueryFilterService()
