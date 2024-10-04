from .info import *
from .utils import *
import copy
import array
import pickle
import atexit

values_stack = [{}]
values = values_stack[-1]
values_global = values_stack[0]

class char:
    def __init__(self, value):
        self.val = value

def nscope():
    global values
    t = {
        "_global":values_global
    }
    if values_stack:
        t["_nonlocal"] = values_stack[-1]
    values_stack.append(t)
    values = values_stack[-1]

def pscope():
    global values
    values_stack.pop()
    values = values_stack[-1]

def rget(dct, name, sep="."):
    path = [*enumerate(name.split(sep), 1)][::-1]
    last = len(path)
    node = dct
    while path:
        pos, name = path.pop()
        if pos != last and name in node and isinstance(node[name], dict):
            node = node[name]
        elif pos == last and name in node:
            return node[name]
        else:
            return bstate("nil")
    return bstate("nil")

def rset(dct, name, value, sep="."):
    path = [*enumerate(name.split(sep), 1)][::-1]
    last = len(path)
    node = dct
    while path:
        pos, name = path.pop()
        if pos != last and name in node and isinstance(node[name], dict):
            node = node[name]
        elif pos == last:
            node[name] = value

includes = set()

class bstate:
    def __init__(self, name):
        self.name = name
    def __eq__(self, other):
        if not isinstance(other, bstate):
            return False
        return other.name == self.name
    def __ne__(self, other):
        return not self == other
    def __repr__(self):
        return f"bstate({self.name!r})"

def expr_preruntime(arg):
    if arg.endswith("i") and arg[:-1].replace("-", "").isdigit():
        return int(arg[:-1])
    elif arg.endswith("f") and arg[:-1].replace("-", "").replace(".", "").isdigit():
        return float(arg[:-1])
    elif arg == "true":
        return 1
    elif arg == "false":
        return 0
    elif arg == "nil":
        return bstate("nil")
    elif arg == "none":
        return bstate("none")
    elif arg == "@space":
        return char(" ")
    elif arg == "@tab":
        return char("\t")
    elif arg == "@empty":
        return char("")
    return arg

def expr_runtime(arg):
    if isinstance(arg, char):
        return arg.val
    elif not isinstance(arg, str):
        return arg
    arg = arg.strip()
    if arg.replace(".", "").replace("_", "").isalnum():
        return arg
    elif arg.startswith("%") and arg[1:].replace(".", "").replace("_", "").isalnum():
        return rget(values, arg[1:])
    return bstate("nil")

def evaluate(expression):
    if expression and expression[0] == "list":
        return compress(expression[1:])
    match (expression):
        case [op1, "==", op2]:
            return expr_runtime(op1) == expr_runtime(op2)
        case [op1, "!=", op2]:
            return expr_runtime(op1) != expr_runtime(op2)
        case [op1, ">", op2]:
            return expr_runtime(op1) > expr_runtime(op2)
        case [op1, "<", op2]:
            return expr_runtime(op1) > expr_runtime(op2)
        case [op1, ">=", op2]:
            return expr_runtime(op1) >= expr_runtime(op2)
        case [op1, "<=", op2]:
            return expr_runtime(op1) >= expr_runtime(op2)
        case ["not", op1]:
            return not expr_runtime(op1)
        case [op1, "or", op2]:
            return expr_runtime(op1) or expr_runtime(op2)
        case [op1, "and", op2]:
            return expr_runtime(op1) and expr_runtime(op2)
        case [op1, "+", op2]:
            return expr_runtime(op1) + expr_runtime(op2)
        case [op1, "-", op2]:
            return expr_runtime(op1) - expr_runtime(op2)
        case [op1, "*", op2]:
            return expr_runtime(op1) * expr_runtime(op2)
        case [op1, "/", op2]:
            return expr_runtime(op1) / expr_runtime(op2)
        case [op1, "%", op2]:
            return expr_runtime(op1) % expr_runtime(op2)
        case [op1, "^", op2]:
            return expr_runtime(op1) ** expr_runtime(op2)
        case ["len-of", op1]:
            value = expr_runtime(op1)
            if hasattr(value, "__len__"):
                return len(value)
            else:
                return bstate("nil")
        case ["join", delim, *values]:
            values, = *map(expr_runtime, values),
            return str(exprs_runtime((delim,))[0]).join(map(str, values))
        case _:
            return bstate("nil")

def exprs_runtime(args):
    put = []
    res = []
    p = 0
    while p < len(args):
        c = args[p]
        if c == "\"":
            c = ""
            p += 1
            put.clear()
            while p < len(args) and not c.endswith("\""):
                c = args[p]; put.append(c); p += 1
            p -= 1
            text = " ".join(put)[:-1]
            for c, r in CHARS.items():
                text = text.replace(c, r)
            res.append(text.replace("\\[quote]", "\""))
        elif c == "(":
            c = ""
            p += 1
            put.clear()
            while p < len(args) and c != ")":
                c = args[p]; put.append(c); p += 1
            p -= 1
            put.pop()
            res.append(evaluate(put))
        elif c == "((":
            c = ""
            p += 1
            put.clear()
            while p < len(args) and c != "))":
                c = args[p]; put.append(c); p += 1
            p -= 1
            put.pop()
            repeatition, *parts = put
            res.append(compress([*exprs_runtime(parts)]*expr_runtime(repeatition)))
        elif c == "'":
            c = ""
            p += 1
            put.clear()
            while p < len(args) and not c.endswith("'"):
                c = args[p]; put.append(c); p += 1
            p -= 1
            text = " ".join(put)[:-1]
            for c, r in CHARS.items():
                text = text.replace(c, r)
            res.append(text.replace("\\[quote]", "'"))
        else:
            res.append(expr_runtime(c))
        p += 1
    return *res,

def exprs_preruntime(args):
    return *map(expr_preruntime, args),

def process(code, name=MAIN_NAME):
    res = []
    oname = name
    c = enumerate(code.split("\n"), 1)
    for lp, line in c:
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        elif line.startswith("#"):
            line = line[1:].strip()
            if line.startswith("!"):
                pass
            elif line:
                ins, arg = line.split(maxsplit=1) if " " in line else (line, None)
                if ins == "include" and arg is not None:
                    if arg.startswith('<') and arg.endswith('>'):
                        arg = os.path.join(LIBDIR, arg[1:-1])
                    elif arg.startswith('"') and arg.endswith('"'):
                        arg = arg[1:-1]
                    if not os.path.isfile(arg):
                        print(f"\nError on line {lp} in file `{name}`\nFile {arg!r} does not exist.")
                        break
                    if arg not in includes:
                        includes.add(name)
                    else:
                        continue
                    res.extend(process(open(arg).read(), arg))
                elif ins == "chname" and arg is not None:
                    if name != MAIN_NAME:
                        name = arg
                elif ins == "force.chname" and arg is not None:
                    name = arg
                elif ins == "define" and arg is not None:
                    if arg in includes:
                        return tuple()
                    else:
                        includes.add(arg)
                elif ins == "doNotShowTime" and arg is None:
                    atexit.unregister(TIME_ELAPSED)
                else:
                    print(f"\nError on line {lp} in file `{name}`\nInvalid directory: {ins}")
                    exit(1)
            else:
                print(f"\nError on line {lp} in file `{name}`\nInvalid directory: {ins}")
                exit(1)
        else:
            ins, *args = line.split()
            args = exprs_preruntime(args)
            res.append((lp, name, ins, args))
    else:
        return tuple(res)
    exit(1)

def run(code):
    if isinstance(code, str):
        code = process(code)
    p = 0
    while p < len(code):
        pos, file, ins, args = code[p]
        args = *exprs_runtime(args),
        argc = len(args)
        # vars
        if ins == "set" and argc == 2:
            rset(values, args[0], args[1])
        # functions
        elif ins == "fn" and argc >= 1:
            temp = []
            name = args[0]
            oargs = args
            opos = pos
            ofile = file
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction not closed!")
                break
            if file != MAIN_NAME:
                name = mangle(file, name)
            rset(values, name, (file, temp, oargs[1:], {}))
        elif ins == "md" and argc >= 2:
            temp = []
            obj = args[0]
            method = args[1]
            arguments = args[2:]
            opos = pos
            ofile = file
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction not closed!")
                break
            if file != MAIN_NAME:
                name = mangle(file, name)
            rset(values, method, (file, temp, arguments, obj))
        elif ins == "define" and argc == 2:
            t, name = args
            if t == "static":
                funcs[name] = (file, tuple())
            elif t == "dynamic":
                if file != MAIN_NAME:
                    name = mangle(file, name)
                funcs[name] = (file, tuple(), tuple())
            else:
                print(f"\nError on line {pos} in file `{file}`\nFunction type {t!r} unknown!")
        elif ins == "ifmain" and argc == 0:
            temp = []
            opos = pos
            ofile = file
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf main function not closed!")
                break
            if file != MAIN_NAME:
                p += 1
                continue
            try:
                err = run(temp)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction raised an error!")
                break
            elif err == -1:
                return err
        elif ins == "ifsetup" and argc == 0:
            temp = []
            opos = pos
            ofile = file
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf main function not closed!")
                break
            if file != SETUP_NAME:
                p += 1
                continue
            try:
                err = run(temp)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction raised an error!")
                break
            elif err == -1:
                return err
        elif ins == "notmain" and argc == 0:
            temp = []
            opos = pos
            ofile = file
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf main function not closed!")
                break
            if file == MAIN_NAME:
                p += 1
                continue
            try:
                err = run(temp)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction raised an error!")
                break
            elif err == -1:
                return err
        elif ins == "call" and argc >= 1:
            fn = rget(values, args[0])
            if fn == bstate("nil"):
                print(f"\nError on line {pos} in file `{file}`\nInvalid function: {name}")
                break
            try:
                nscope()
                for k, value in zip(fn[2], args[1:]):
                    values[k] = value
                values["_self"] = fn[3]
                err = run(fn[1])
                pscope()
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {pos} in file `{file}`\nFunction raised an error!")
                break
            elif err == -1:
                return err
        elif ins == "return" and argc == 2:
            rset(values, "_nonlocal."+args[0], args[1])
        # classes
        elif ins == "state" and argc == 1:
            name = str(args[0])
            rset(values, name, {
                "_instance":{
                    "name":name,
                    "type":"type:"+name
                }
            })
        elif ins == "copy" and argc == 2:
            rset(values, args[1], copy.deepcopy(rget(values, args[0])))
        # if statements
        elif ins == "iftrue" and argc == 1:
            temp = []
            opos = pos
            ofile = file
            oargs = args
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf function not closed!")
                break
            if not oargs[0]:
                p += 1
                continue
            try:
                err = run(temp)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {opos} in file `{ofile}`\nIf function raised an error!")
                break
            elif err == -1:
                return err
        elif ins == "iffalse" and argc == 1:
            temp = []
            opos = pos
            ofile = file
            oargs = args
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf function not closed!")
                break
            if oargs[0]:
                p += 1
                continue
            try:
                err = run(temp)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {opos} in file `{ofile}`\nIf function raised an error!")
                break
            elif err == -1:
                return err
        # loops
        elif ins == "irange" and argc == 2:
            values[arg[0]] = tuple(range(args[1]+1))
        elif ins == "range" and argc == 2:
            values[arg[0]] = tuple(range(args[2]))
        elif ins == "foreach" and argc == 2:
            temp = []
            opos = pos
            ofile = file
            oargs = args
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFor function not closed!")
                break
            if not stack:
                p += 1
                continue
            try:
                for i in oargs[1]:
                    values[oargs[0]] = i
                    try:
                        err = run(temp)
                    except (SystemExit, KeyboardInterrupt):
                        raise
                    except Exception as e:
                        print(repr(e))
                        break
                    if err > 0:
                        break
                    elif err == -1:
                        raise StopIteration()
                else:
                    p += 1
                    continue
                break
            except StopIteration:
                pass
        elif ins == "for" and argc == 2:
            temp = []
            opos = pos
            ofile = file
            oargs = args
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFor function not closed!")
                break
            try:
                for i in tuple(range(oargs[1])):
                    values[oargs[0]] = i
                    try:
                        err = run(temp)
                    except (SystemExit, KeyboardInterrupt):
                        raise
                    except Exception as e:
                        print(repr(e))
                        break
                    if err > 0:
                        break
                    elif err == -1:
                        raise StopIteration()
                else:
                    p += 1
                    continue
                break
            except StopIteration:
                pass
        elif ins == "ufor" and argc == 1:
            temp = []
            opos = pos
            ofile = file
            oargs = args
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFor function not closed!")
                break
            try:
                for i in tuple(range(oargs[0])):
                    try:
                        err = run(temp)
                    except (SystemExit, KeyboardInterrupt):
                        raise
                    except StopIteration:
                        pass
                    except Exception as e:
                        print(repr(e))
                        break
                    if err > 0:
                        break
                    elif err == -1:
                        raise StopIteration()
                else:
                    p += 1
                    continue
                break
            except StopIteration:
                pass
        elif ins == "loop" and argc == 0:
            temp = []
            opos = pos
            ofile = file
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFor function not closed!")
                break
            ok = True
            while ok:
                try:
                    err = run(temp)
                except (SystemExit, KeyboardInterrupt):
                    raise
                except StopIteration:
                    pass
                except Exception as e:
                    print(repr(e))
                    break
                if err > 0:
                    break
                elif err == -1:
                    ok = False
            else:
                p+=1
                continue
            break
        # libs
        elif ins == "cache" and argc == 1:
            name = args[0]
            with open(name, "wb") as f:
                f.write(pickle.dumps(funcs))
        elif ins == "load" and (argc == 1 or argc == 2):
            with open(args[0], "rb") as f:
                fs = pickle.loads(f.read())
                if argc == 2:
                    fs = {f"{args[1]}.{name}":code for name, code in fs.items()}
                funcs.update(fs)
        elif ins == "module" and argc == 1:
            temp = []
            opos = pos
            oargs = args
            p += 1
            k = 1
            while p < len(code):
                pos, _, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, oargs[0] if file != MAIN_NAME else mangle(file, oargs[0]), ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{file}`\nInline module not closed!")
                break
            try:
                err = run(temp)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {opos} in file `{file}`\nInline module raised an error!")
                break
            elif err == -1:
                return err
        elif ins == "setup" and argc == 0:
            with open(args[0], "r") as f:
                name = SETUP_NAME
                x = process(f.read(), name)
                fs = {}
                if run(x, funcs=fs):
                    print(f"\nError on line {pos} in file `{file}`\nFunction {name!r} raised an error!")
                    break
                funcs.update(fs)
        elif ins == "exec" and argc == 1:
            ofile = file
            file = args[0]
            if not os.path.isfile(file):
                print(f"\nError on line {pos} in file `{ofile}`\nCouldnt find {file!r}")
                break
            with open(file) as f:
                run(f.read())
        # system
        elif ins == "system" and argc == 2:
            values[oargs[0]] = os.system(args[1])
        elif ins == "system:getenv" and argc == 1:
            values[oargs[0]] = os.getenv(args[0], bstate("nil"))
        # io
        elif ins == "print":
            print(*args, end='')
        elif ins == "println":
            print(*args)
        elif ins == "input" and argc == 1:
            values[args[0]] = input()
        # type casting
        elif ins == "toint" and argc == 2:
            try:
                values[args[0]] = int(args[1])
            except:
                print(f"\nError on line {pos} in file `{file}`\nCouldnt convert {args[0]!r} to int!")
                break
        elif ins == "tofloat" and argc == 2:
            try:
                values[args[0]] = float(args[1])
            except:
                print(f"\nError on line {pos} in file `{file}`\nCouldnt convert {args[0]!r} to int!")
                break
        elif ins == "tostring" and argc == 2:
            values[args[0]] = str(args[1])
        # errors
        elif ins == "panic" and argc == 0:
            print(f"\nError on line {pos} in file `{file}`\nPanic!")
            break
        elif ins == "stop" and argc == 0:
            return -1
        else:
            print(f"\nError on line {pos} in file `{file}`\nInvalid instruction: {ins}\nArguments: {' '.join(map(repr, args))}")
            break
        p += 1
    else:
        return 0
    return 1