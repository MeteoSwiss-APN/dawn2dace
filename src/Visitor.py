
from collections.abc import Iterable
from Intermediates import *

D2D_Classes = (
    Stencil,
    Init,
    Loop,
    Map,
    StencilNode,
    MultiStage,
    Stage,
    DoMethod,
    K_Interval,
    K_Section,
    Statement
)


def iter_fields(node):
    """
    Yield a tuple of ``(fieldname, value)`` for each field in ``node._fields``
    that is present on *node*.
    """
    for field in dir(node):
        try:
            yield field, getattr(node, field)
        except AttributeError:
            pass


class D2D_Visitor:
    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        visitor(node)

    def visit_list(self, node: list):
        for n in node:
            if isinstance(n, D2D_Classes):
                self.visit(n)

    def generic_visit(self, node):
        for field, value in iter_fields(node):
            if field.startswith('_'):
                continue
            if isinstance(value, D2D_Classes):
                self.visit(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, D2D_Classes):
                        self.visit(item)


class D2D_Transformer(D2D_Visitor):
    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def visit_list(self, node: list):
        new_list = []
        for n in node:
            if isinstance(n, D2D_Classes):
                novum = self.visit(n)
                if novum is not None:
                    new_list.append(novum)
        return new_list

    def generic_visit(self, node):
        for field, old_value in iter_fields(node):
            if field.startswith('_'):
                continue
            if isinstance(old_value, D2D_Classes):
                new_node = self.visit(old_value)
                if new_node is None:
                    delattr(node, field)
                else:
                    old_value = new_node
            elif isinstance(old_value, Iterable):
                for o in old_value:
                    if isinstance(o, D2D_Classes):
                        new_node = self.visit(o)
                        if new_node is None:
                            delattr(node, field)
                        else:
                            o = new_node
        return node
