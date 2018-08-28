#!/usr/bin/env python
# -*- coding: utf-8 -*-
import itertools
import operator
import datetime
import math

def stringify(iter):
    return ','.join(map(str, list(iter)))

def get_all_subclasses(cls):
    all_subclasses = set()

    for subclass in cls.__subclasses__():
        all_subclasses.add(subclass)
        all_subclasses.update(get_all_subclasses(subclass))

def groupby_sorted(items, attr):
    return itertools.groupby(
        sorted(items, key=operator.attrgetter(attr)),
        key=operator.attrgetter(attr),
    )

def groupby_sorted_dict(items, attr):
    return itertools.groupby(
        sorted(items, key=operator.itemgetter(attr)),
        key=operator.itemgetter(attr),
    )


def year_delta(a, b):
    return datetime.datetime(a.year+b, a.month, a.day)

quarter_map = {
    0: 1,
    1: 4,
    2: 7,
    3: 10
}

def last_day_of_month(date):
    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month+1, day=1) - datetime.timedelta(days=1)

def quarter_delta(a, b):
    q = int(math.ceil(a.month/3.))
    month = quarter_map.get((q + b - 1)%4)
    year = a.year + (b - q/4)/4 + q/4
    try:
        return datetime.datetime(year, month, a.day)
    except ValueError:
        return last_day_of_month(datetime.datetime(year, month, 1))

def month_delta(a, b):
    year = a.year + (a.month + b - 1) / 12
    month = (a.month + b) % 12 or 12
    from dateutil import relativedelta
    try:
        return a + relativedelta.relativedelta(months=b)
    except ValueError:
        return last_day_of_month(datetime.datetime(year, month, 1))

def week_delta(a, b):
    a += datetime.timedelta(weeks=b)
    return datetime.datetime(a.year, a.month, a.day)

def day_delta(a, b):
    a += datetime.timedelta(days=b)
    return datetime.datetime(a.year, a.month, a.day)

def get_date_by_interval(itv_type, itv_value):
    delta_func = globals().get('%s_delta' % itv_type)
    if not delta_func:
        raise ValueError('Unknow time interval type')

    now = datetime.datetime.now()
    itv_value = int(itv_value)
    date = delta_func(now, itv_value)
    return datetime.datetime(date.year, date.month, date.day)

