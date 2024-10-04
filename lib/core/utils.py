import array, os

def minimize(lst, py=False):
    lst = list(lst)
    if len(lst) == 0:
        return []
    k = [[lst[0], 1]]
    if len(lst) == 1:
        return lst
    for i in lst[1:]:
        if i == k[-1][0]:
            k[-1][1] += 1
        else:
            k.append([i, 1])
    return [(f'[{item}] * {count}' if not py else f'*[{item}]*{count}') if count > 1 else item for item, count in k]

def my_sum(args):
    if not args:
        return args
    else:
        start = type(args[0])()
        for i in args:
            start += i
        return start

def sources(code):
    src = set()
    for _, name, _, _ in code:
        src.add(name)
    return *src,

def compress(lst):
    types = set()
    for i in lst:
        types.add(type(i))
    if len(types) == 1 and (int in types or float in types):
        return array.array("i" if int in types else "f", lst)
    else:
        return lst

def mangle(file, name):
    return f"{os.path.basename(file).split('.', 1)[0]}.{name}"