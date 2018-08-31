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
import datetime
from django.db.models import Q
from calendar import monthrange
from mirrors.common.utils import get_date_by_interval
import operator


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
        if connect_op == 'AND':
            return node1 & node2
        else:
            return node1 | node2
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
        import ipdb; ipdb.set_trace()
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

def get_field_part(parser):
    return parser.lookup.rsplit('__', 1)[0]

def _r_min_ago(n):
    return datetime.datetime.now() - datetime.timedelta(seconds=n * 60)


def _rd(n):
    return datetime.date.today() + datetime.timedelta(days=n)


def yr_l(n):
    return datetime.datetime(year=n, month=1, day=1)


def yr_h(n):
    return datetime.datetime.combine(
        datetime.date(year=n, month=12, day=31),
        datetime.time.max,
    )

def get_this_week():
    today = datetime.date.today()
    monday = today + datetime.timedelta(days=-today.weekday())
    sunday = monday + datetime.timedelta(days=7)
    calendar_start_day = 1
    if calendar_start_day == 0:
        monday += datetime.timedelta(days=-1)
        sunday = monday + datetime.timedelta(days=7)
    return monday, sunday

def get_last_week():
    monday, sunday = get_this_week()
    last_week_delta = datetime.timedelta(days=7)
    return monday - last_week_delta, sunday - last_week_delta


def get_next_week():
    monday, sunday = get_this_week()
    next_week_delta = datetime.timedelta(days=7)
    return monday + next_week_delta, sunday + next_week_delta

def get_this_month():
    today = datetime.date.today()
    firstday = datetime.datetime(today.year, today.month, 1)
    lastday = datetime.datetime(
        today.year,
        today.month,
        1,
    ) + datetime.timedelta(days=monthrange(today.year, today.month)[1])
    return firstday, lastday

def get_last_month():
    today = datetime.date.today()
    lastday = datetime.datetime(today.year, today.month, 1)
    last_month_last_day = lastday - datetime.timedelta(seconds=1)
    firstday = datetime.datetime(
        last_month_last_day.year,
        last_month_last_day.month,
        1,
    )
    return firstday, lastday

def get_next_month():
    from dateutil import relativedelta
    today = datetime.date.today()
    next_month = today + relativedelta.relativedelta(months=1)
    firstday = datetime.datetime(next_month.year, next_month.month, 1)
    lastday = firstday + relativedelta.relativedelta(months=1)
    return firstday, lastday

def get_this_quarter():
    today = datetime.date.today()
    q = (today.month - 1) / 3

    firstday = datetime.datetime(today.year, q * 3 + 1, 1)
    if q == 3:
        year = today.year + 1
        month = 1
    else:
        year = today.year
        month = (q + 1) * 3 + 1
    lastday = datetime.datetime(year, month, 1) - datetime.timedelta(seconds=1)
    return firstday, lastday


def get_last_quarter():
    today = datetime.date.today()
    q = (today.month - 1) / 3

    lastday = datetime.datetime(
        today.year,
        q * 3 + 1,
        1,
    ) - datetime.timedelta(seconds=1)
    if q == 0:
        year = today.year - 1
        month = 10
    else:
        year = today.year
        month = (q - 1) * 3 + 1

    firstday = datetime.datetime(year, month, 1)
    return firstday, lastday


def get_next_quarter():
    from dateutil import rrule, relativedelta
    today = datetime.datetime.today()
    rr = rrule.rrule(
        rrule.DAILY,
        bymonth=(1, 4, 7, 10),
        bymonthday=1,
        dtstart=today,
    )
    start_day = rr.after(today, inc=False).date()
    firstday = datetime.datetime(start_day.year, start_day.month, 1)
    lastday = firstday + relativedelta.relativedelta(
        months=3,) - datetime.timedelta(seconds=1)
    return firstday, lastday

def get_last_year():
    today = datetime.date.today()
    firstday = datetime.datetime(today.year - 1, 1, 1)
    lastday = datetime.datetime(
        today.year,
        1,
        1,
    ) - datetime.timedelta(seconds=1)
    return firstday, lastday


class FilterPrepMeta(type):
    def __init__(cls, *args, **kwargs):
        processors = cls.dynamic_gen_past_future_time_processor()
        for func_name, func in processors.items():
            setattr(cls, func_name, func)
        super(FilterPrepMeta, cls).__init__(*args, **kwargs)

    def gen_q(cls, field, query_info):
        raise NotImplementedError

    def get_field_part(cls, lookup_parser):
        raise NotImplementedError

    def gen_time_processor(cls, type, op, positive=True):
        
        def lte_proc(lookup_parser, value):
            if value > 0:
                start = datetime.datetime.now()
                end = get_date_by_interval(type, value)
                end = end + datetime.timedelta(days=1)
            else:
                end = datetime.datetime.now()
                start = get_date_by_interval(type, value)
            field = cls.get_field_part(lookup_parser)
            return cls.gen_q(field, {
                'gte': start,
                'lt': end
            })

        def gte_proc(lookup_parser, value):
            date = get_date_by_interval(type, value)
            field = cls.get_field_part(lookup_parser)
            if value > 0:
                return cls.gen_q(field, {
                    'gte': date,
                })
            else:
                date = date + datetime.timedelta(days=1)
                return cls.gen_q(field, {
                    'lte': date,
                })

        def processor(self, lookup_parser, values):
            value = int(values[0])
            if not positive:
                value = -value
            if op == 'day_gte':
                return gte_proc(lookup_parser, value)
            else:
                return lte_proc(lookup_parser, value)
        return processor

    refs = ['past', 'future']
    operator_types = ['day_gte', 'day_lte']
    time_types = ['year', 'quarter', 'month', 'week', 'day']

    lookup_types = None
    fields_to_lookups = None

    def dynamic_gen_past_future_time_processor(cls):
        processors = {}
        for ref in cls.refs:
            for op_type in cls.operator_types:
                for time_type in cls.time_types:
                    operator = '%s_%s_%s' % (ref, time_type, op_type)
                    func_name = 'process_%s' % operator
                    processors[func_name] = cls.gen_time_processor(time_type, op_type, ref=='future')
                    cls.lookup_types[operator] = operator
                    cls.fields_to_lookups['datetime'].append(operator)
        return processors



class PeeweeFilterPrepMeta(FilterPrepMeta):
    lookup_types = LOOKUP_TYPES
    fields_to_lookups = FIELDS_TO_LOOKUPS

    def get_field_part(cls, lookup_parser):
        return get_field_part(lookup_parser)

    def gen_q(cls, field, query_info):
        kwargs = {
            '%s__%s' % (field, op): val for op, val in query_info.items()
        }
        return [kwargs]


class FilterPreprocessor(object):
    __metaclass__ = PeeweeFilterPrepMeta

    def get_field_model(self, parser):
        
        model = parser.get_lookup_info()[0]
        if model:
            field = model._meta.fields[parser.lookup_field]
            if isinstance(field, models.ForeignKey):
                return field.to
        return model

    def get_field_obj(self, parser):
        model = parser.get_lookup_info()[0]
        if model:
            return model._meta.fields[parser.lookup_field]

    def get_process_key(self, parser):
        return 'process_%s' % (parser.lookup_operator or parser.lookup.rsplit('__', 1)[1])

    def process_lookup(self, lookup_parser, values=None):
        process_key = self.get_process_key(lookup_parser)
        if hasattr(self, process_key):
            return getattr(self, process_key)(lookup_parser, values)

        return [{lookup_parser.lookup: v} for v in values]

    def process_isnull(self, lookup_parser, values):
        value = values[0]
        model = lookup_parser.get_lookup_info()[0]
        field_str = get_field_part(lookup_parser)
        if model:
            field = model._meta.fields[lookup_parser.lookup_field]
            if isinstance(field, models.CharField):
                return Q(**{'%s__isnull' % field_str: value}) | Q(**{field_str: ''})
        return [{'%s__isnull' % field_str: value}]

    def process_s(self, lookup_parser, values):
        return [{'%s__in' % get_field_part(lookup_parser): values}]

    def process_in(self, lookup_parser, values):
        return [{'%s__in' % get_field_part(lookup_parser): values}]

    def process_ns(self, lookup_parser, values):
        return [{'%s__nin' % get_field_part(lookup_parser): values}]

    def process_nin(self, lookup_parser, values):
        return [{'%s__nin' % get_field_part(lookup_parser): values}]

    def process_date_is(self, lookup_parser, values):
        return [{
            '%s__gte' % get_field_part(lookup_parser): yr_l(int(value)),
            '%s__lte' % get_field_part(lookup_parser): yr_h(int(value)),
        } for value in values]

    def process_day_lte(self, lookup_parser, values):
        date = datetime.datetime.strptime(values[0], "%Y-%m-%d") + datetime.timedelta(days=1)
        return [{'%s__lt' % get_field_part(lookup_parser): date}]

    def process_day_gte(self, lookup_parser, values):
        date = datetime.datetime.strptime(values[0], "%Y-%m-%d")
        return [{'%s__gte' % get_field_part(lookup_parser): date}]

    def process_today(self, lookup_parser, values):
        return [{
            '%s__gte' % get_field_part(lookup_parser): _rd(0),
            '%s__lt' % get_field_part(lookup_parser): _rd(1),
        }]

    def process_yesterday(self, lookup_parser, values):
        return [{
            '%s__gte' % get_field_part(lookup_parser): _rd(-1),
            '%s__lt' % get_field_part(lookup_parser): _rd(0),
        }]

    def process_this_week(self, lookup_parser, values):
        monday, sunday = get_this_week()
        return [{
            '%s__gte' % get_field_part(lookup_parser): monday,
            '%s__lt' % get_field_part(lookup_parser): sunday,
        }]

    def process_last_week(self, lookup_parser, values):
        monday, sunday = get_last_week()
        return [{
            '%s__gte' % get_field_part(lookup_parser): monday,
            '%s__lt' % get_field_part(lookup_parser): sunday,
        }]

    def process_next_week(self, lookup_parser, values):
        monday, sunday = get_next_week()
        return [{
            '%s__gte' % get_field_part(lookup_parser): monday,
            '%s__lt' % get_field_part(lookup_parser): sunday,
        }]

    def process_altran_this_week(self, lookup_parser, values):
        today = datetime.date.today()
        firstday_of_week = today + datetime.timedelta(days=-today.weekday()-2)
        lastday_of_week = firstday_of_week + datetime.timedelta(days=7)
        return [{
            '%s__gte' % get_field_part(lookup_parser): firstday_of_week,
            '%s__lt' % get_field_part(lookup_parser): lastday_of_week,
        }]

    def process_altran_last_week(self, lookup_parser, values):
        today = datetime.date.today()
        firstday_of_week = today + datetime.timedelta(days=-today.weekday() - 2 -7)
        lastday_of_week = firstday_of_week + datetime.timedelta(days=7)
        return [{
            '%s__gte' % get_field_part(lookup_parser): firstday_of_week,
            '%s__lt' % get_field_part(lookup_parser): lastday_of_week,
        }]

    def process_this_month(self, lookup_parser, values):
        firstday, lastday = get_this_month()
        return [{
            '%s__gte' % get_field_part(lookup_parser): firstday,
            '%s__lt' % get_field_part(lookup_parser): lastday,
        }]

    def process_last_month(self, lookup_parser, values):
        firstday, lastday = get_last_month()
        return [{
            '%s__gte' % get_field_part(lookup_parser): firstday,
            '%s__lt' % get_field_part(lookup_parser): lastday,
        }]

    def process_next_month(self, lookup_parser, values):
        firstday, lastday = get_next_month()
        return [{
            '%s__gte' % get_field_part(lookup_parser): firstday,
            '%s__lt' % get_field_part(lookup_parser): lastday,
        }]

    def process_three_days_ago(self, lookup_parser, values):
        return [{
            '%s__lt' % get_field_part(lookup_parser): _rd(-3),
        }]

    def process_next_seven_days(self, lookup_parser, values):
        return [{
            '%s__gte' % get_field_part(lookup_parser): _rd(1),
            '%s__lte' % get_field_part(lookup_parser): _rd(8)
        }]

    def process_next_thirty_days(self, lookup_parser, values):
        return [{
            '%s__gte' % get_field_part(lookup_parser): _rd(1),
            '%s__lte' % get_field_part(lookup_parser): _rd(31)
        }]

    def process_one_week_ago(self, lookup_parser, values):
        return [{
            '%s__lt' % get_field_part(lookup_parser): _rd(-7),
        }]

    def process_two_weeks_ago(self, lookup_parser, values):
        return [{
            '%s__lt' % get_field_part(lookup_parser): _rd(-14),
        }]

    def process_one_month_ago(self, lookup_parser, values):
        return [{
            '%s__lt' % get_field_part(lookup_parser): _rd(-30),
        }]

    def process_three_months_ago(self, lookup_parser, values):
        return [{
            '%s__lt' % get_field_part(lookup_parser): _rd(-90),
        }]

    def process_six_months_ago(self, lookup_parser, values):
        return [{
            '%s__lt' % get_field_part(lookup_parser): _rd(-183),
        }]

    def process_this_quarter(self, lookup_parser, values):
        firstday, lastday = get_this_quarter()
        return [{
            '%s__gte' % get_field_part(lookup_parser): firstday,
            '%s__lte' % get_field_part(lookup_parser): lastday,
        }]

    def process_last_quarter(self, lookup_parser, values):
        firstday, lastday = get_last_quarter()
        return [{
            '%s__gte' % get_field_part(lookup_parser): firstday,
            '%s__lte' % get_field_part(lookup_parser): lastday,
        }]

    def process_next_quarter(self, lookup_parser, values):
        firstday, lastday = get_next_quarter()
        return [{
            '%s__gte' % get_field_part(lookup_parser): firstday,
            '%s__lte' % get_field_part(lookup_parser): lastday,
        }]

    def process_this_year_to_this_month(self, lookup_parser, values):
        now = datetime.datetime.now()
        firstday, lastday = get_next_month()
        return [{
            '%s__gte' % get_field_part(lookup_parser): datetime.datetime(now.year, 1, 1),
            '%s__lte' % get_field_part(lookup_parser): firstday - datetime.timedelta(seconds=1)
        }]

    def process_this_year(self, lookup_parser, values):
        now = datetime.datetime.now()
        return [{
            '%s__gte' % get_field_part(lookup_parser): datetime.datetime(now.year, 1, 1),
            '%s__lte' % get_field_part(lookup_parser): datetime.datetime(now.year + 1, 1, 1)
                                                        - datetime.timedelta(seconds=1)
        }]

    def process_last_year(self, lookup_parser, values):
        firstday, lastday = get_last_year()
        return [{
            '%s__gte' % get_field_part(lookup_parser): firstday,
            '%s__lt' % get_field_part(lookup_parser): lastday,
        }]
    
    def process_one_year_ago(self, lookup_parser, values):
        return [{
            '%s__lt' % get_field_part(lookup_parser): _rd(-365),
        }]

    def process_in_one_year(self, lookup_parser, values):
        return [{
            '%s__gt' % get_field_part(lookup_parser): _rd(-365),
        }]

    def process_lte_days_ago(self, lookup_parser, values):
        return [{
            '%s__gte' % get_field_part(lookup_parser): _rd(-1 * int(value) + 1),
        } for value in values]

    def process_gte_days_ago(self, lookup_parser, values):
        return [{
            '%s__lte' % get_field_part(lookup_parser): _rd(-1 * int(value) + 1),
        } for value in values]

    def process_year_eq(self, lookup_parser, values):
        return [{
            '%s__gte' % get_field_part(lookup_parser): yr_l(int(value)),
            '%s__lte' % get_field_part(lookup_parser): yr_h(int(value)),
        } for value in values]

    def process_year_lt(self, lookup_parser, values):
        return [{
            '%s__lt' % get_field_part(lookup_parser): yr_l(int(value)),
        } for value in values]

    def process_year_gt(self, lookup_parser, values):
        return [{
            '%s__gte' % get_field_part(lookup_parser): yr_l(int(value)),
        } for value in values]

    def process_until_today(self, lookup_parser, values):
        return [{
            '%s__lte' % get_field_part(lookup_parser): _rd(1),
        }]

    def process_until_this_week(self, lookup_parser, values):
        monday, sunday = get_this_week()
        return [{
            '%s__lte' % get_field_part(lookup_parser): sunday,
        }]

    def process_until_this_month(self, lookup_parser, values):
        firstday, lastday = get_this_month()
        return [{
            '%s__lte' % get_field_part(lookup_parser): lastday,
        }]

    def _process_inheritance(self, lookup_parser, values, getter):
        from mirrors.models import InheritanceMixin
        model = self.get_field_model(lookup_parser)
        if issubclass(model, InheritanceMixin):
            ids_group = [
                getter(ins) for ins in model.objects.filter(id__in=values)
            ]
            ids = [0]
            if ids_group:
                ids = reduce(operator.add, ids_group)
            return [{
                '%s__in' % get_field_part(lookup_parser) : ids
            }]
        return []

    def process_children(self, lookup_parser, values):
        return self._process_inheritance(lookup_parser, values, lambda x: x.children)

    def process_parent(self, lookup_parser, values):
        return self._process_inheritance(lookup_parser, values, lambda x: x.parents)

    def process_next_range_days(self, lookup_parser, values):
        return [{
            '%s__gte' % get_field_part(lookup_parser): _rd(1),
            '%s__lte' % get_field_part(lookup_parser): _rd(1 * int(value) + 1),
        } for value in values]


class ValuePreprocessor(object):
    def get_process_key(self, parser):
        model, lookup_field, lookup_operator = parser.get_lookup_info()
        return 'process_%s' % INV_FIELD_TYPES[type(model._meta.get_field(lookup_field))]

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
        self.lookup_model = None
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

        self.lookup_model = curr

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
        model_or_doc = self.lookup_model or self.model_or_doc
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
            rel_field = lookup_field
            on = None
            curr_meta_related_objects = {
                '{0}'.format(_.name): _
                for _ in curr._meta.related_objects
            }
            curr_meta_fields = {
                _.name: _ for _ in curr._meta.fields
            }
            if rel_field in curr_meta_fields:
                field_obj = curr_meta_fields[rel_field]
                if isinstance(field_obj, models.ForeignKey):
                    on = field_obj.name
                    joined = field_obj.related_model
                else:
                    return
            else:
                if rel_field in curr_meta_related_objects:
                    joined = curr_meta_related_objects[rel_field].related_model
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
        curr_meta_related_objects = {
            '{0}'.format(_.name): _
            for _ in model._meta.related_objects
        }
        curr_meta_fields = {
            _.name: _ for _ in model._meta.fields
        }
        if lookup in curr_meta_related_objects:
            lookup = curr_meta_related_objects[lookup]

        if lookup not in curr_meta_fields:
            return
        return lookup

    def parse_lookup_operator(self, model, lookup, lookup_type):
        curr_meta_fields = {
            _.name: _ for _ in model._meta.fields
        }
        field_obj = curr_meta_fields.get(lookup)
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
        query.where.add(q_node, 'AND')
        return query


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
            curr_meta_fields = {
                _.name: _ for _ in curr._meta.fields
            }
            if len(suf_lookups) == 2 \
                    and suf_lookups[0] not in curr_meta_fields:
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
