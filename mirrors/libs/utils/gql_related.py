import json
import re

from jinja2.loaders import BaseLoader
from werkzeug.datastructures import ImmutableMultiDict
from jinja2.sandbox import ImmutableSandboxedEnvironment

import decimal
from mirrors.common.logger import logger

class DjangoLoader(BaseLoader):

    def __init__(self):
        pass

    def get_source(self, environment, _):
        return _, None, None


variable_repr_re = re.compile(r'\{\{(.*?)\}\}')


def find_used_variable(content):
    matched = variable_repr_re.findall(content)
    return [each.split('.')[0] for each in matched]


def str_to_obj(str):
    return json.loads(str)


default_jinja_context = {
    "len": len,
    'float': float,
    'decimal': decimal.Decimal,
    'str_to_obj': str_to_obj,
}


def jinja_render(content, context):
    if not content:
        content = {}
    from jinja2.runtime import Undefined
    env = ImmutableSandboxedEnvironment(
        loader=DjangoLoader(),
        cache_size=0,
        undefined=Undefined,
    )
    context.update(default_jinja_context)
    try:
        return env.get_template(content).render(context)
    except Exception as e:
        logger.debug('----- render content failed -----')
        logger.debug(content)
        logger.debug('--------------- end -------------')
        import traceback
        traceback.print_exc()
        raise


def jinja_render_many(arr, context):
    _SPLITER = '^#^#^'
    content = _SPLITER.join(arr)
    ret = jinja_render(content, context)
    return tuple(ret.split(_SPLITER))


def gql_render(str, context=None):
    return str


def parse_gql(gql, model, custom_query_model=None):
    from mirrors.libs.advance_search.parser import Parser
    from mirrors.libs.advance_search.advsearch_visitor import AdvSearchVisitor, AdvSearchRewriteVisitor
    ast = Parser.parse(gql)
    # 防止前端传错误的gql，进行重写
    visitor = AdvSearchRewriteVisitor()
    ast = ast.accept(visitor)

    visitor = AdvSearchVisitor(model, custom_query_model)
    node = ast.accept(visitor)
    if node:
        node = node.to_query_node(model)
    return node

def extract_args_or_gql(request_args, key):
    if key in request_args:
        return request_args[key]
    gql = request_args.get('gql')
    if not gql:
        return None
    gql += '&'
    re_str = r'\b{0}(__eq|__s)?=(-*\w+)\b'.format(key)
    match = re.search(re_str, gql)
    if match:
        return match.group(2)
    else:
        return None


class TrackerDict(ImmutableMultiDict):

    def __init__(self, *args, **kwargs):
        self.keys = set()
        super(TrackerDict, self).__init__(*args, **kwargs)

    def tracker(self, func):

        def wrapper(*args, **kwargs):
            if len(args):
                key = args[0]
            else:
                key = kwargs.get('key')
            self.keys.add(key)
            return func(*args, **kwargs)

        return wrapper

    def __getitem__(self, item):
        self.keys.add(item)
        return super(TrackerDict, self).__getitem__(item)

    def __getattribute__(self, item):
        attr = super(TrackerDict, self).__getattribute__(item)
        if item in ('get', 'getlist'):
            attr = self.tracker(attr)
        return attr
