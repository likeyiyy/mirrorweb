# coding: utf-8
from functools import reduce

from django.db.models.sql import Query

from mirrors.common.orm import and_connector, JoinInfo
from django.utils import tree
from django.db.models import Q, QuerySet
from .visitor import BaseVisitor
from mirrors.libs.advance_search.parser import AttrAST, AndAST, OrAST, NotAST
from mirrors.common.logger import logger

class BaseRewriteVisitor(BaseVisitor):

    def visit_attr(self, ast):
        return ast

    def visit_or(self, ast):
        new_ast = OrAST()
        for child in ast.children:
            new_ast.add_child(child.accept(self))
        return new_ast

    def visit_and(self, ast):
        new_ast = AndAST()
        for child in ast.children:
            new_ast.add_child(child.accept(self))
        return new_ast

    def visit_not(self, ast):
        return NotAST(ast.ast.accept(self))


class AdvSearchRewriteVisitor(BaseRewriteVisitor):

    def visit_attr(self, ast):
        key = ast.key
        if key.endswith('__ne'):
            # （ne）转化为 （not eq）来处理
            new_ast = ast.clone()
            new_ast.key = new_ast.key[:-4] + '__eq'
            ast = NotAST(new_ast)
        elif key.endswith('_set__isnull'):
            # 前端可能传过来错误的搜索条件，例如note_set__isnull
            ast = ast.clone()
            ast.key = ast.key[:-6] + 'id__isnull'
        return ast


class TreeNode(object):

    def __init__(self, key, val):
        self.key = key
        self.val = list(val)
        self.children = {}

    def get_children(self):
        return self.children.values()

    def add_child(self, child):
        if child.key in self.children:
            value = self.children[child.key]
            value.val.extend(child.val)
            child_children = child.get_children()
            for c_child in child_children:
                value.add_child(c_child)
        else:
            self.children[child.key] = child

    def is_leaf(self):
        return not bool(self.children)

    def merge(self, other):
        if self.key != other.key:
            return False

        for child in other.get_children():
            self.add_child(child)
        return True


class QueryTreeNode(object):
    '''
    关联query_node和TreeNode
    '''

    def __init__(self, query_node, tree_node):
        self.query_node = query_node
        self.tree_nodes = []
        if tree_node:
            self.tree_nodes.append(tree_node)

    def connect(self, rhs, operator, merge_tree=True):
        assert isinstance(rhs, type(self))
        if not self.tree_nodes:
            self.tree_nodes = rhs.tree_nodes
        elif rhs.tree_nodes:
            if merge_tree:
                self.tree_nodes[0].merge(rhs.tree_nodes[0])
            else:
                self.tree_nodes.extend(rhs.tree_nodes)
        self.query_node = self.query_node.connect(rhs.query_node, operator)
        return self

    def invert(self):
        self.query_node = ~self.query_node
        return self

    def fix_dup_join_models(self, tree_node, joined_models):
        from mirrors.common.orm import alias as alias_gen
        join_infos = tree_node.val
        if join_infos:
            model_proxy = join_infos[0].join_model
            if model_proxy.model in joined_models:
                new_model = alias_gen(model_proxy.model)
                for j_info in join_infos:
                    j_info.join_model.model = new_model
            else:
                joined_models.add(model_proxy.model)
    
        for child in tree_node.get_children():
            self.fix_dup_join_models(child, joined_models)

    def remove_model_proxy_from_tree(self, tree_node):
        join_infos = tree_node.val
        if join_infos:
            for j_info in join_infos:
                model = j_info.model
                if isinstance(model, ModelProxy):
                    j_info.model = model.model
            
                join_model = j_info.join_model
                if isinstance(join_model, ModelProxy):
                    j_info.join_model = join_model.model
    
        for child in tree_node.get_children():
            self.remove_model_proxy_from_tree(child)

    def rebuild_tree(self, query, tree_nodes):
        # 为重复join的model自动生成别名
        joined_models = {query.model}
        for tree_node in tree_nodes:
            self.fix_dup_join_models(tree_node, joined_models)

        # 还原model proxy为model
        for tree_node in tree_nodes:
            self.remove_model_proxy_from_tree(tree_node)

    def rebuild_query_node(self, query_node):

        def remove_model_proxy_from_q(q_node):

            def remove_model_proxy(q_node):
                model = q_node.model
                if isinstance(model, ModelProxy):
                    q_node.model = model.model

            modify_query_node(q_node, remove_model_proxy)

        # 还原query_node的model proxy为model
        remove_model_proxy_from_q(query_node)

    def apply_tree_nodes(self, query, tree_nodes):

        def follow_joins_by_tree(query, tree_node):
            join_infos = tree_node.val
            if join_infos:
                query = join_infos[0].apply(query)

            for child in tree_node.get_children():
                query = follow_joins_by_tree(query, child)
            return query

        for tree_node in tree_nodes:
            query = follow_joins_by_tree(query, tree_node)
        return query

    def apply_query_node(self, query, query_node):
        return query.where(query_node)

    def apply(self, query):
        if self.tree_nodes:
            self.rebuild_tree(query, self.tree_nodes)
        if self.query_node:
            self.rebuild_query_node(self.query_node)

        if self.tree_nodes:
            query = self.apply_tree_nodes(query, self.tree_nodes)
        if self.query_node:
            query = self.apply_query_node(query, self.query_node)
        return query

    def to_query_node(self, model):
        query = model.objects.all()
        query = self.apply(query)
        if query.where:
            query_node = reduce(and_connector, query.where)
        else:
            query_node = None
        return query_node

    def has_reverse_join(self):

        def is_reverse_join(join_info):
            model = join_info.model
            if isinstance(model, ModelProxy):
                model = model.model
            join_model = join_info.join_model
            if isinstance(join_model, ModelProxy):
                join_model = join_model.model
            if model._meta.get_reverse_related_field_for_model(join_model):
                return True
            return False

        def verify_tree(tree_node):
            if tree_node.val:
                join_info = tree_node.val[0]
                if is_reverse_join(join_info):
                    return True

            for child in tree_node.get_children():
                if verify_tree(child):
                    return True
            return False

        tree_nodes = self.tree_nodes
        if tree_nodes:
            if len(tree_nodes) > 1:
                return True

            if verify_tree(tree_nodes[0]):
                return True
        return False


class ModelProxy(object):

    def __init__(self, model):
        self.model = model


def modify_query_node(query_node, callback):

    def modify_node_or_q(node_or_q, callback):
        if isinstance(node_or_q, tree.Node):
            for child in node_or_q.children:
                modify_node_or_q(child, callback)
        elif isinstance(node_or_q, Q):
            callback(node_or_q)

    modify_node_or_q(query_node, callback)


def query_joins_to_join_infos(current, joins):
    result = []
    if current not in joins:
        return result

    for model, join_type, on in joins[current]:
        result.append(
            JoinInfo(
                model=current,
                join_model=model,
                join_type=join_type,
                on=on,
            ),)
        result.extend(query_joins_to_join_infos(model, joins))
    return result


class AdvSelectQuery(Query):
    _joins = {}
    _joined_models = []
    
    def join(self, model, join_type=None, on=None, alias=None):
        assert alias is None, 'AdvSelectQuery join does not support alias!'
        if model in self._joined_models or model == self.model:
            raise Exception('custom query filter不支持重复join同一个model')
        return super(AdvSelectQuery, self).join(model, join_type, on)


class AdvSearchVisitor(BaseVisitor):

    def __init__(self, model, custom_query_model=None):
        self.model = model
        self.custom_query_model = custom_query_model

    def get_simple_query(self):
        return self.model.select()

    def _make_tree_node(self, query_model, keys, joins, custom_joins):
        assert len(keys) == len(joins)

        top_nodes = []
        tree_nodes = {}
        for join in custom_joins:
            model = join.model
            if isinstance(model, ModelProxy):
                model = model.model

            join_model = join.join_model
            if isinstance(join_model, ModelProxy):
                join_model = join_model.model

            key = join_model.__name__
            node = TreeNode(key, [join])
            if model == query_model:
                top_nodes.append(node)
            else:
                parent_node = tree_nodes[model]
                parent_node.add_child(node)
            tree_nodes[join_model] = node

        index = -1
        last_node = None
        for key in reversed(keys):
            if last_node is None:
                last_node = TreeNode(key, [joins[index]])
                for node in top_nodes:
                    last_node.add_child(node)
            else:
                ast = TreeNode(key, [joins[index]])
                ast.add_child(last_node)
                last_node = ast
            index -= 1

        root = TreeNode(None, [])
        if last_node:
            root.add_child(last_node)
        else:
            for node in top_nodes:
                root.add_child(node)
        return root

    def _compile_query(self, model_proxy, query):

        def find_custom_join(joins):
            for j_info in joins:
                on = j_info.on
                if on and ('{' in on or '.' in on):
                    # hard code的on条件一般包含"{model}" or "t1."等字符
                    return True
            return False

        model_proxy_map = {model_proxy.model: model_proxy}

        def modify_query_node_model_proxy(query_node):

            def replace_to_model_proxy(q_node):
                if q_node.model in model_proxy_map:
                    q_node.model = model_proxy_map[q_node.model]

            modify_query_node(query_node, replace_to_model_proxy)

        def modify_joins_model_proxy(joins):
            for j_info in joins:
                if j_info.model in model_proxy_map:
                    j_info.model = model_proxy_map[j_info.model]

                if j_info.join_model not in model_proxy_map:
                    model_proxy_map[j_info.join_model] = ModelProxy(
                        j_info.join_model,)
                j_info.join_model = model_proxy_map[j_info.join_model]

        joins = query_joins_to_join_infos(query.model, query._joins)

        if find_custom_join(joins):
            # 如果join中有hard code的on/alias, 改写为子查询
            query.query = ['id']
            where = Q(_model=query.model, id__in=query)
            return where, []
        
        where = reduce(and_connector, [query.where])

        # 将joins中的model替换为model proxy
        modify_joins_model_proxy(joins)

        # 将query_node中的model替换为model proxy
        modify_query_node_model_proxy(where)
        return where, joins
    
    def _visit_attr(self, ast, model):
        from mirrors.common.orm import CustomRegisterLookupParser
        from mirrors.libs.custom_filter.cqf import custom_query_filter_service
    
        key = ast.key
        value = self.decode_value(ast.val)
        parser = CustomRegisterLookupParser(
            model,
            key,
            custom_query_filter_service,
        )
        parser.parse()
        if not parser.is_valid_lookup():
            return
    
        query = AdvSelectQuery(parser.lookup_model_or_doc)
        query = parser.filter_query([value], query)
        if not len(query.where):
            logger.warning('Unknown Attr Query:', key, value)
            return
    
        key_items = key.split('__')
        if key_items[-1] == parser.lookup_operator:
            key_items = key_items[:-2]
        else:
            key_items = key_items[:-1]
    
        # 所有的joined model替换为代理对象，最后apply的时候再还原；
        joins = []
        if parser.joins:
            model_proxy = None
            for join in parser.joins:
                if model_proxy:
                    curr = model_proxy
                else:
                    curr = join['curr']
                model_proxy = ModelProxy(join['be_joined'])
                joins.append(
                    JoinInfo(
                        model=curr,
                        join_model=model_proxy,
                        on=join['curr_field'],
                    ), )
        else:
            model_proxy = ModelProxy(query.model)
    
        where, custom_joins = self._compile_query(model_proxy, query)
    
        tree_node = self._make_tree_node(
            query.model,
            key_items,
            joins,
            custom_joins,
        )
        return QueryTreeNode(where, tree_node)

    def visit_attr(self, ast):
        return self._visit_attr(ast, self.model)

    def _visit_children_ast(self, ast, operator):
        nodes = []
        merge_tree = True
        for child in ast.children:
            node = child.accept(self)
            if not node:
                continue
        
            if not isinstance(child, AttrAST) \
                and node.has_reverse_join():
                merge_tree = False
            nodes.append(node)
    
        if not nodes:
            return
    
        ret = nodes[0]
        for node in nodes[1:]:
            ret = ret.connect(node, operator, merge_tree)
        return ret

    def visit_or(self, ast):
        return self._visit_children_ast(ast, 'OR')

    def visit_and(self, ast):
        return self._visit_children_ast(ast, 'AND')

    def visit_not(self, ast):
        query_node = ast.ast.accept(self)
        if not query_node:
            return

        if query_node.has_reverse_join():
            # 如果not语句中包含反向join，则转换为子查询处理
            query = self.model.select(['id'])
            query = query_node.apply(query)
            q_node = ~Q(_model=self.model, id__in=query)
            return QueryTreeNode(q_node, None)

        return query_node.invert()

