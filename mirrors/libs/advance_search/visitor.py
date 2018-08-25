class BaseVisitor(object):

    def decode_value(self, value):
        from mirrors.libs.utils import gql_render
        value = (value or '').strip()
        value = gql_render(value)
        value = value.decode('utf8')
        return value

    def ast_to_args(self, ast):
        from werkzeug.datastructures import ImmutableMultiDict
        return ImmutableMultiDict({ast.key: self.decode_value(ast.val)})

    def visit_or(self, ast):
        raise NotImplementedError

    def visit_and(self, ast):
        raise NotImplementedError

    def visit_attr(self, ast):
        raise NotImplementedError

    def visit_not(self, ast):
        raise NotImplementedError
