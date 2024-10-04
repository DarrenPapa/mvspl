# Pleade do not modify carelessly.
# This file can only be modified by the author.
# This file will contain code that follows standards
# specifically for it and thus might introduce compat
# problems when modified.

# SBPL PYTHON API 0.0.1
# This file will be maintained separately.

# For more documentation please see
# ./lib/core/docs/DarrenPapa/p2s_api.txt

from . import parser
from . import info
from .utils import mangle
import os

functions = {}
stack = parser.stack

def run(code):
    "Run SBPL code."
    try:
        return parser.run(code, funcs=functions)
    except:
        return 1

def call(name, *args, calling_from=info.MAIN_NAME):
    "Call a function."
    stack.extend(args)
    name = name if calling_from == info.MAIN_NAME else mangle(calling_from, name)
    if name not in functions:
        return 1
    return run(functions[name][1])

def parse_sbpl_expr(arg):
    "Parse arguments."
    return parser.exprs_preruntime(arg.strip().split())

def parse_sbpl_expr_runtime(arg):
    "Parse arguments, the stack being able to change the states of some values."
    return parser.exprs_runtime(parse_sbpl_expr(arg))

def to_sbpl(value):
    "Convert python types to SBPL types."
    if isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, float):
        return f"{value}f"
    elif isinstance(value, int):
        return f"{value}i"
    elif isinstance(value, str):
        return f'" {value}"'
    elif isinstance(value, list):
        return f"(( 1i {' '.join(map(to_sbpl, value))} ))"
    elif value is None:
        return "none"
    else:
        return "nil"

class Stack:
    def push(arg):
        stack.append(arg)
    def pop():
        return stack.pop() if stack else parser.bstate('nil')
    def peek():
        return stack[-1] if stack else parser.bstate('nil')
    def dupe():
        Stack.push(Stack.peek())
    def rot():
        a, b = Stack.pop(), Stack.pop()
        stack.extend([a, b])

def test():
    # Testing calling functions
    run("""
    sfn test
        println top
    end
    """)
    call("test", "test") # test
    # Testing arguments
    print(parse_sbpl_expr("90i top")) # 90, 'top'
    print(parse_sbpl_expr_runtime("90i top")) # 90, bstate('nil')
    # Testing conversion
    print("str:", to_sbpl("test"))
    print("int:", to_sbpl(138))
    print("float:", to_sbpl(13.8))
    print("list:", to_sbpl([0, 1, 1.0, None, True, False, {}]))
    # Stack manipulation
    Stack.push("Hello, world!")
    Stack.push(90)
    Stack.rot()
    Stack.dupe()
    call("test") # Hello, world!
    print("Peek:", Stack.peek()) # Peek: Hello, world!
    print("Pop:", Stack.pop()) # Pop: Hello, world!
    print("Pop:", Stack.pop()) # Pop: 90