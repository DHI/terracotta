"""expressions.py

Safe execution of user-supplied math expressions
"""

from typing import Mapping, Dict, Tuple, Callable, Union, Optional, Type, Any
import ast
import timeit
import operator

import numpy as np


EXTRA_CALLABLES = {
    # name: (callable, nargs)
    'where': (np.where, 3),
    'minimum': (np.minimum, 2),
    'maximum': (np.maximum, 2),
    'abs': (np.abs, 1),
    'mod': (np.mod, 1),
    'sqrt': (np.sqrt, 1),
    'log': (np.log, 1),
    'log10': (np.log10, 1),
    'exp': (np.exp, 1),
    'sin': (np.sin, 1),
    'cos': (np.cos, 1),
    'tan': (np.tan, 1),
    'sinh': (np.sinh, 1),
    'cosh': (np.cosh, 1),
    'tanh': (np.tanh, 1),
    'arcsin': (np.arcsin, 1),
    'arccos': (np.arccos, 1),
    'arctan': (np.arctan, 1),
    'arcsinh': (np.arcsinh, 1),
    'arccosh': (np.arccosh, 1),
    'arctanh': (np.arctanh, 1)
}

EXTRA_CONSTANTS = {
    'pi': np.pi
}


class ParseException(Exception):
    pass


class ExpressionParser(ast.NodeVisitor):
    NODE_TO_BINOP: Dict[Type[ast.operator], Callable] = {
        # math
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,

        # logic
        ast.BitAnd: operator.and_,
        ast.BitOr: operator.or_,
    }

    NODE_TO_UNOP: Dict[Type[ast.unaryop], Callable] = {
        ast.Invert: operator.invert
    }

    NODE_TO_COMPOP: Dict[Type[ast.cmpop], Callable] = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
    }

    def __init__(self,
                 constants: Mapping[str, Any] = None,
                 callables: Mapping[str, Tuple[Callable, int]] = None,
                 timeout: Union[float, int] = None):
        self.timeout = timeout
        self._start_time: Optional[float] = None

        if constants is None:
            constants = {}

        self.constants = constants

        if callables is None:
            callables = {}

        self.callables = callables

    def execute(self, node: ast.AST) -> Any:
        self._start_time = timeit.default_timer()
        return self.visit(node)

    def visit(self, node: ast.AST) -> Any:
        if self.timeout is not None:
            if self._start_time is None:
                raise RuntimeError('visit() cannot be called directly; '
                                   'use execute() to parse expression')

            if timeit.default_timer() - self._start_time > self.timeout:
                raise ParseException('timeout during expression execution')

        return super().visit(node)

    def generic_visit(self, node: ast.AST) -> None:
        # only visit allowed nodes
        raise ParseException(f'{type(node).__name__} not allowed in expressions')

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in self.constants:
            return self.constants[node.id]

        if node.id in self.callables:
            # return (function_name, callable, num_args)
            return (node.id, *self.callables[node.id])

        raise ParseException(f'unrecognized name \'{node.id}\' in expression')

    def visit_Call(self, node: ast.Call) -> Any:
        funcname, func, nargs = self.visit(node.func)
        got_nargs = len(node.args)
        if got_nargs != nargs:
            raise ParseException(
                f'wrong number of arguments for function {funcname} '
                f'(got {got_nargs}, expected {nargs})'
            )
        return func(*map(self.visit, node.args))

    def visit_Num(self, node: ast.Num) -> Any:
        return node.n

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        op_callable = ExpressionParser.NODE_TO_UNOP[type(node.op)]
        return op_callable(self.visit(node.operand))

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        op_callable = ExpressionParser.NODE_TO_BINOP[type(node.op)]
        return op_callable(self.visit(node.left), self.visit(node.right))

    def visit_Compare(self, node: ast.Compare) -> Any:
        if len(node.ops) > 1:
            raise ParseException('chained comparisons are not supported')
        op_callable = ExpressionParser.NODE_TO_COMPOP[type(node.ops[0])]
        return op_callable(self.visit(node.left), self.visit(node.comparators[0]))


def evaluate_expression(expr: str,
                        operands: Mapping[str, np.ndarray]) -> np.ndarray:
    eval_constants = dict(**operands, **EXTRA_CONSTANTS)

    try:
        expr_ast = ast.parse(expr, filename='<expression>', mode='eval')
    except SyntaxError as exc:
        raise ValueError(f'given string {expr} is not a valid expression') from exc

    parser = ExpressionParser(eval_constants, EXTRA_CALLABLES, timeout=1)

    try:
        result = parser.execute(expr_ast)
    except ParseException as exc:
        raise ValueError(str(exc)) from None
    except Exception as exc:
        # pass only exception message to not leak traceback
        raise ValueError(f'unexpected error while evaluating expression: {exc!s}') from None

    if not isinstance(result, np.ndarray):
        raise ValueError('expression does not return an array')

    return result
