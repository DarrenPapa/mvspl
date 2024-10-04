#!/usr/bin/env python3

# Please do not modify as this is the cli interface
# for sbpl to run.
# Failure to abide to this rule will fall under
# copyright infridgement.

# See LICENSE.txt

import os, sys, atexit

TIME_ELAPSED = lambda: print(f"\nTime Elapsed (s): {time.time()-START:,.8f}\n{message_good}\n")

LD = os.path.dirname(sys.argv[0])
LIBD = os.path.join(LD, "lib")
CORED = os.path.join(LIBD, "core")
COREDD = os.path.join(CORED, "docs")
COREDDD = os.path.join(COREDD, "core")

if not os.path.isdir(LIBD):
    os.mkdir(LIBD)
    print("[INFO]: Created directory `lib`")
    os.mkdir(CORED)
    print("[INFO]: Created directory `lib/core`\nPlease install the core library.")
    os.mkdir(COREDD)
    print("[INFO]: Created directory `lib/core/docs`\nPlease install the core library.")
    os.mkdir(COREDDD)
    print("[INFO]: Created directory `lib/core/docs/core`\nPlease install the core library.")

try:
    from lib.core.parser import run
    from lib.core.info import *
    from lib.core.utils import *
except Exception as e:
    print(f"[ERROR]: Something happened while importing core lib!\n{repr(e)}")
    exit(1)

def main():
    for pos, val in enumerate(sys.argv[1:]):
        if val.startswith("--"):
            flags.add(val[2:])
        else:
            break
    if flags:
        sys.argv = [sys.argv[0], *sys.argv[pos+1:]]
        if flags - known_flags:
            print("Unknown flags:", ", ".join(flags - known_flags))
    if "verbose" in flags:
        print("Flags:", flags)
        print(f"Interpreter: {os.path.abspath(sys.argv[0])}")
        if len(sys.argv) >= 2:
            print(f"File: {os.path.abspath(sys.argv[1])}")
    if "version" in flags or "ver" in flags:
        print("Version:", VERSION)
    argc = len(sys.argv)
    if argc >= 2:
        ff = {}
        with open(sys.argv[1]) as f:
            code = f.read()
            if "setup" in flags:
                code = process(code, name="__setup__")
            atexit.register(TIME_ELAPSED)
            try:
                if run(code):
                    print("\nFinished with an error!")
                    if "bully" in flags:
                        print(message_bad)
                    exit(3)
                else:
                    if "main-entry" in flags:
                        if "verbose" in flags:
                            print("Automatically calling main...\n")
                            flags.remove("verbose")
                        if run("call main"):
                            print("\nMain Entry: Finished with an error!")
                            if "bully" in flags:
                                print(message_bad)
                            exit(3)
            except (SystemExit, KeyboardInterrupt):
                raise
            except StopIteration:
                raise
    else:
        print(f"REPL - SBPL {VERSION}")
        f = {}
        while True:
            act = input(">>> ")
            if act and act.split(maxsplit=1)[0] in INC:
                t = [act]
                while True:
                    act = input("... ")
                    if act == ".done":
                        break
                    t.append(act)
                act = "\n".join(t)
            elif act == ".paste":
                print("Paste Mode")
                t = []
                while True:
                    act = input()
                    if act == ".done":
                        break
                    t.append(act)
                act = "\n".join(t)
            if act == "exit":
                break
            elif act == ".editor":
                act = []
                print("Basic REPL In-memory Editor.\nEnter '.exit' to stop.\nEnter '.run' to execute code.\n'.help' for more.")
                while True:
                    a = input(f"+++ ")
                    if a == ".exit":
                        break
                    elif a == ".back":
                        if act:
                            act.pop()
                        else:
                            print("No lines left.")
                    elif a == ".clear":
                        act.clear()
                    elif a == ".run":
                        stack.clear()
                        if run("\n".join(act)):
                            print("Error!")
                    elif a == ".load":
                        print("Load a file. '*' to cancel.")
                        while True:
                            file = input("? ")
                            if not os.path.isfile(file):
                                print("Invalid file path!")
                            elif file == "*":
                                break
                            else:
                                with open(file) as f:
                                    stack.extend(f.read().split("\n"))
                    elif a == ".remove":
                        while True:
                            line = input(f"1-{len(act)}, '*' to cancel: ").strip()
                            if not line.isdigit():
                                print("Not a digit!")
                            elif line == "*":
                                break
                            else:
                                line = int(line)-1
                                if line in tuple(range(len(act))):
                                    act.pop(line)
                                    break
                                else:
                                    print("Line out of range!")
                    elif a == ".show":
                        while True:
                            line = input(f"1-{len(act)}, '*' to cancel: ").strip()
                            if not line.isdigit():
                                print("Not a digit!")
                            elif line == "*":
                                break
                            else:
                                line = int(line)-1
                                if line in tuple(range(len(act))):
                                    print(act[line])
                                    break
                                else:
                                    print("Line out of range!")
                    elif a == ".rshow":
                        while True:
                            line = input(f"1-{len(act)}, '*' to cancel: ").strip()
                            if not line.isdigit():
                                print("Not a digit!")
                            elif line == "*":
                                break
                            else:
                                line = int(line)-1
                                if line in tuple(range(len(act))):
                                    print("\n".join(act[line:line+10]))
                                    break
                                else:
                                    print("Line out of range!")
                    elif a == ".help":
                        print("'.list' List lines.\n'.back' Erase previouly entered line.\n'.remove' Remove a specific line.\n'.show' Print a specific line.\n'.rshow' Show the specified line with the next 10 available lines.\n'.clear' Delete every line.")
                    elif a == ".list":
                        mlen = len(str(len(act)))+1
                        for i, line in enumerate(act, 1):
                            print(f"{str(i).rjust(mlen)} | {line}")
                    else:
                        act.append(a)
            elif act.startswith("$"):
                code = os.system(act[1:])
                print(f"Error Code: {'success' if not code else code}")
            else:
                if run(act):
                    print("Error!")

if __name__ == "__main__":
    main()
