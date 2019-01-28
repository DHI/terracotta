"""expressions.py

Safe execution of user-supplied expressions
"""

from typing import Mapping
import ast

import numpy as np

ALLOWED_NODES = (
    # expressions
    ast.Expression,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,

    # math operators
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.Pow,
    ast.Num,

    # comparisons
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,

    # logic
    ast.Invert,
    ast.BitAnd,
    ast.BitOr,
)

NUMPY_BUILTINS = (
    'where',
    'minimum',
    'maximum',
    'abs',
    'mod',
    'sqrt',
    'log',
    'log10',
    'exp',
    'sin',
    'cos',
    'tan',
    'sinh',
    'cosh',
    'tanh',
    'arcsin',
    'arccos',
    'arctan',
    'arcsinh',
    'arccosh',
    'arctanh',
    'pi',
)


def evaluate_expression(expr: str,
                        operands: Mapping[str, np.ndarray]) -> np.ndarray:
    try:
        expr_ast = ast.parse(expr, filename='<expression>', mode='eval')
    except SyntaxError:
        raise ValueError(f'given string {expr} is not a valid expression')

    # make sure expression is safe to execute
    for node in ast.walk(expr_ast):
        nodeclass = type(node)

        if nodeclass not in ALLOWED_NODES:
            raise ValueError(f'{nodeclass.__name__} not allowed in expressions')

        if isinstance(node, ast.Name):
            if node.id not in operands and node.id not in NUMPY_BUILTINS:
                raise ValueError(f'unrecognized name \'{node.id}\' in expression')

    eval_locals = {fun: getattr(np, fun) for fun in NUMPY_BUILTINS}
    eval_locals.update(operands)

    expr_bytecode = compile(expr_ast, filename='<expression>', mode='eval')
    try:
        result = eval(
            expr_bytecode,
            {'__builtins__': dict()},
            eval_locals
        )
    except Exception as exc:
        # pass only exception message to not leak traceback
        raise ValueError(f'unexpected error while evaluating expression: {exc!s}')

    if not isinstance(result, np.ndarray):
        raise ValueError('expression does not return an array')

    return result
