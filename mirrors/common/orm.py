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
from functools import reduce

from django.db.models import Q


class ModelProxyMixin(type):
    """将派生出来的 model 没有的属性都代理到 原始的 model 上"""

    def __getattr__(cls, name):
        return getattr(cls._real_model, name)


def alias(model):
    """用于 peewee 的 self join，生成原 model 的别名 model
    ::example
        >> u2 = alias(User)
        >> User.select().join(u2, ('filed_a', 'field_b'))
    :param model: 原 model
    :return: 别名 model """

    from six import with_metaclass
    return type(model.__name__, (with_metaclass(ModelProxyMixin),),
                {'_real_model': model})

def node_connector(connect_op='AND'):

    def connector(node1, node2):
        if node1 is None:
            return node2
        if node2 is None:
            return node1
        return node1.connect(node2, connect_op)

    return connector


class JoinInfo(object):

    def __init__(
            self,
            model=None,
            join_model=None,
            join_type=None,
            on=None,
            alias=None,
    ):
        self.model = model
        self.join_model = join_model
        self.join_type = join_type
        self.on = on
        self.alias = alias

    def apply(self, query):
        if self.model:
            query = query.switch(self.model)
        return query.join(self.join_model, self.join_type, self.on, self.alias)


and_connector = node_connector('AND')
or_connector = node_connector('OR')

LOOKUP_TYPES = {
    's': 'id in',
    'ns': 'id not in',
    'eq': 'equal to',
    'lt': 'less than',
    'gt': 'greater than',
    'lte': 'less than or equal to',
    'gte': 'greater than or equal to',
    'day_lte': 'less than or equal to',
    'day_gte': 'greater than or equal to',
    'ne': 'not equal to',
    'istartswith': 'starts with',
    'endswith': 'ends with',
    'icontains': 'contains',
    'in': 'is one of',
    'nin': 'not in',
    'isnull': 'is null',
    'find_in_set': 'find_in_set',

    # special lookups that require some preprocessing
    'to_date': 'to_date',
    'today': 'is today',
    'yesterday': 'is yesterday',
    'this_week': 'this week',
    'last_week': 'last week',
    'next_week': 'next week',
    'this_month': 'this month',
    'last_month': 'last month',
    'next_month': 'next month',
    'this_quarter': 'this quarter',
    'last_quarter': 'last quarter',
    'next_quarter': 'next quarter',
    'last_ten_week': 'last ten week',
    'last_ten_month': 'last ten moon',
    'this_year': 'this year',
    'last_year': 'last year',
    'three_days_ago': '> 3 days',
    'next_seven_days': 'next 7 days',
    'next_thirty_days': 'next 30 days',
    'one_week_ago': '> 1 week',
    'two_weeks_ago': '> 2 weeks',
    'one_month_ago': '> 1 month',
    'three_months_ago': '> 3 months',
    'six_months_ago': '> 6 months',
    'one_year_ago': '> 1 year',
    'in_one_year': '< 1 year',
    'lte_days_ago': 'less than ... days ago',
    'gte_days_ago': 'greater than ... days ago',
    'year_eq': 'year is',
    'year_lt': 'year is less than...',
    'year_gt': 'year is greater than...',
    'until_today': 'until today',
    'until_this_week': 'until this week',
    'until_this_month': 'until this month',

    'children': 'children',
    'parent': 'parent',

    'poset_gte': 'poset_gte',
    'poset_lte': 'poset_lte',

    #very hard hardcode
    'altran_this_week': 'altran_this_week',
    'altran_last_week': 'altran_last_week',

    'next_range_days': 'next ... days',

}

FIELD_TYPES = {
    'foreign_key': [models.ForeignKey],
    'text': [models.CharField, models.TextField],
    'numeric': [models.IntegerField, models.FloatField, models.DecimalField],
    'boolean': [models.BooleanField],
    'datetime': [models.DateTimeField, models.DateField],
    'time': [models.TimeField],
}

INV_FIELD_TYPES = dict((v, k) for k in FIELD_TYPES for v in FIELD_TYPES[k])

FIELDS_TO_LOOKUPS = {
    'foreign_key': ['eq', 'in', 's', 'isnull', 'nin', 'ns', 'ne', 'children', 'parent'],
    'text': ['eq', 'icontains', 'istartswith', 'endswith', 'in', 'ne', 's', 'isnull', 'nin', 'ns', 'poset_gte',
             'poset_lte', 'find_in_set'],
    'numeric': ['eq', 'ne', 'lt', 'lte', 'gt', 'gte', 'in', 's', 'isnull', 'nin', 'ns', 'children', 'parent'],
    'boolean': ['eq', 'isnull', 's'],
    'datetime': ['eq', 'to_date', 'lt', 'gt', 'gte', 'lte', 'day_gte', 'day_lte', 'today', 'yesterday', 'this_week',
                 'last_week', 'next_week', 'this_month', 'last_month', 'next_month', 'this_year', 'last_year',
                 'three_days_ago', 'next_seven_days', 'next_thirty_days', 'one_week_ago', 'two_weeks_ago', 'one_month_ago', 'three_months_ago',
                 'six_months_ago', 'one_year_ago', 'in_one_year', 'lte_days_ago',
                 'gte_days_ago', 'year_eq', 'year_lt', 'year_gt', 'until_today',
                 'until_this_week', 'until_this_month', 'isnull', 'this_quarter', 'last_quarter',
                 'last_ten_week', 'last_ten_month', 'next_quarter', 'next_range_days'],
    'time': [],
}


class ValuePreprocessor(object):
    def get_process_key(self, parser):
        model, lookup_field, lookup_operator = parser.get_lookup_info()
        return 'process_%s' % INV_FIELD_TYPES[type(model._meta.fields[lookup_field])]

    def split_values(self, values):
        value = values[0]
        if isinstance(value, str):
            values = value.split(',')
        else:
            values = [value]
        return values

    need_split_value_operators = ['s', 'ns', 'children', 'parent']

    def process_value(self, lookup_parser, values=None):
        process_key = self.get_process_key(lookup_parser)
        if lookup_parser.lookup_operator in self.need_split_value_operators:
            values = self.split_values(values)
        if hasattr(self, process_key):
            return getattr(self, process_key)(lookup_parser, values)
        return values

    def process_boolean(self, lookup_parser, values):
        def eval_value(v):
            _map = {
                'true': 1,
                'false': 0,
                '1': 1,
                '0': 0
            }
            return bool(_map.get(v.lower(), v))

        new_values = []
        for v in values:
            new_values.append(eval_value(v))
        return new_values


class LookupParser(object):
    def __init__(self, model_or_doc, lookup):
        self.model_or_doc = model_or_doc
        self.lookup = lookup or ''
        self.joins = []
        self.lookup_field = None
        self.lookup_operator = None
        self.lookup_model_or_doc = None
        self._values = None

    def get_lookup_operators(self, lookups=None):
        return LOOKUP_TYPES.keys()

    def parse(self):
        if not self.model_or_doc or not self.lookup:
            return

        lookups = self.lookup.split('__')
        lookup_type = 'eq'
        if len(lookups) > 1 and lookups[-1] in self.get_lookup_operators(lookups):
            lookup_type = lookups.pop()

        curr = self.parse_lookup_join(self.model_or_doc, lookups)
        if not curr:
            return

        self.lookup_model_or_doc = curr

        lookup = lookups[-1]
        lookup = self.parse_lookup_field(curr, lookup)
        if not lookup:
            return
        self.lookup_field = lookup

        lookup_op = self.parse_lookup_operator(curr, lookup, lookup_type)
        if lookup_op:
            self.lookup_operator = lookup_op

    def parse_lookup_join(self, model, lookups):
        raise NotImplementedError

    def parse_lookup_field(self, model, lookup):
        return NotImplementedError

    def parse_lookup_operator(self, model, lookup, lookup_type):
        return NotImplementedError

    def is_valid_lookup(self):
        return bool(self.lookup_field is not None and self.lookup_operator is not None)

    def apply_joins(self, query):
        raise NotImplementedError

    def get_lookup_info(self):
        model_or_doc = self.lookup_model_or_doc or self.model_or_doc
        return model_or_doc, self.lookup_field, self.lookup_operator
    
    def set_values(self, values):
        self._values = values
        
    def get_values(self):
        return self._values
    
    def get_filter_preprocessor(self):
        raise NotImplementedError

    def get_value_preprocessor(self):
        raise NotImplementedError

    def filter_query(self, values, query):
        raise NotImplementedError

class DjangoLookupParser(LookupParser):
    def parse_lookup_join(self, model, lookups):
        curr = model
        self.joins = []
        for lookup_field in lookups[:-1]:
            if lookup_field in curr._meta.rel_fields:
                rel_field = curr._meta.rel_fields[lookup_field]
            else:
                rel_field = lookup_field

            on = None
            if rel_field in curr._meta.fields:
                field_obj = curr._meta.fields[rel_field]
                if isinstance(field_obj, models.ForeignKey):
                    on = field_obj.name
                    joined = field_obj.to
                else:
                    return
            else:
                if rel_field in curr._meta.reverse_relations:
                    joined = curr._meta.reverse_relations[rel_field]
                else:
                    return

            self.joins.append({
                'curr': curr,
                'be_joined': joined,
                'curr_field': on,
                'be_joined_field': None,
            })
            curr = joined
        return curr

    def parse_lookup_field(self, model, lookup):
        # 基本字段的搜索走这里。
        if lookup in model._meta.rel_fields:
            lookup = model._meta.rel_fields[lookup]

        if lookup not in model._meta.fields:
            return
        return lookup

    def parse_lookup_operator(self, model, lookup, lookup_type):
        field_obj = model._meta.fields.get(lookup)
        if not field_obj or lookup_type not in FIELDS_TO_LOOKUPS[INV_FIELD_TYPES[type(field_obj)]]:
            return
        return lookup_type

    def apply_joins(self, query):
        for item in self.joins:
            query = JoinInfo(
                model=item['curr'],
                join_model=item['be_joined'],
                on=item['curr_field']
            ).apply(query)
        return query
    
    def get_filter_preprocessor(self):
        return FilterPreprocessor()

    def get_value_preprocessor(self):
        return ValuePreprocessor()

    def filter_query(self, values, query):
        v_preprocessor = self.get_value_preprocessor()
        f_preprocessor = self.get_filter_preprocessor()
        
        values = v_preprocessor.process_value(self, values)
        q_kwargs = f_preprocessor.process_lookup(self, values)
        if not q_kwargs:
            return query
        
        nodes = []
        for item in q_kwargs:
            if isinstance(item, dict):
                node = Q(**item)
            else:
                node = item
            nodes.append(node)
        q_node = reduce(and_connector, nodes)
        return query.where(q_node)


class BaseCustomRegLookupParser(LookupParser):
    def __init__(self, model, lookup, query_filter_service):
        self.register_service = query_filter_service
        self.register_manager = self.get_model_manager(model)
        super(BaseCustomRegLookupParser, self).__init__(model, lookup)

    def get_model_manager(self, model):
        raise NotImplementedError

    def get_lookup_operators(self, lookups=None):
        if not lookups:
            return self.register_manager.all_operators | set(LOOKUP_TYPES)

        pre_lookups, suf_lookups = lookups[:-1], lookups[-2:]
        curr = self.parse_lookup_join(self.model_or_doc, pre_lookups)
        if curr:
            if len(suf_lookups) == 2 \
                    and suf_lookups[0] not in curr._meta.fields:
                _curr = self.parse_lookup_join(curr, suf_lookups)
                if _curr:
                    curr = _curr
            manager = self.get_model_manager(curr)
            return manager.get_registered_operators() | set(LOOKUP_TYPES)
        return self.register_manager.all_operators | set(LOOKUP_TYPES)


    def parse_lookup_field(self, model, lookup):
        manager = self.get_model_manager(model)
        if lookup not in manager.get_query_filters_names():
            return
        self.register_manager = manager
        return lookup

    def parse_lookup_operator(self, model, lookup, lookup_type):
        manager = self.get_model_manager(model)
        if not manager.is_valid_operator(lookup, lookup_type):
            return None
        return lookup_type

    def filter_query(self, values, query):
        lookup = '%s__%s' % (self.lookup_field, self.lookup_operator)
        return self.register_manager.filter_query(query, {lookup: values[0]})


class CustomRegisterLookupParser(BaseCustomRegLookupParser, DjangoLookupParser):
    def get_model_manager(self, model):
        if hasattr(model, '_meta'):
            model = model._meta.model_name.lower()
        return self.register_service.manager.get_model_manager(model)
    
    def parse_lookup_field(self, model, lookup):
        ret = BaseCustomRegLookupParser.parse_lookup_field(self, model, lookup)
        if not ret:
            self.register_manager = None
            ret = DjangoLookupParser.parse_lookup_field(self, model, lookup)
        return ret

    def parse_lookup_operator(self, model, lookup, lookup_type):
        ret = BaseCustomRegLookupParser.parse_lookup_operator(self, model, lookup, lookup_type)
        if not ret:
            self.register_manager = None
            ret = DjangoLookupParser.parse_lookup_operator(self, model, lookup, lookup_type)
        return ret

    def filter_query(self, values, query):
        if self.register_manager:
            return BaseCustomRegLookupParser.filter_query(self, values, query)
        else:
            return DjangoLookupParser.filter_query(self, values, query)
