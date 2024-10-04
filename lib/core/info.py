import os, sys, time, random

LOCDIR = os.path.dirname(sys.argv[0])
LIBDIR = os.path.join(LOCDIR, "lib")
CORELIB = os.path.join(LIBDIR, "core")
VERSION = 0.1

# Characters
CHARS = {
    "\\\\":"\\[escape]",
    "\\n":"\n",
    "\\t":"\t",
    "\\s":"\s",
    "\\v":"\v",
    "\\f":"\f",
    "\\r":"\r",
    "\\[win_nl]":"\r\n",
    "\\[unix_nl]":"\n",
    "\\[null]":"\0",
    "\\[escape]":"\\"
}

# For repl to handle and to be able to nest functions.
INC = {
    "md", "fn",
    "ifmain", "ifsetup", "notmain",
    "iftrue", "iffalse",
    "loop", "for", "ufor", "foreach",
    "module"
}

known_flags = {
    "setup", "verbose", "version", "ver", "main-entry",
    "bully"
}

messages_bully = [
    "Fix the damn error!",
    "Its simple really...",
    "WHY CANT YOU DO YOUR JOB!",
    "How can you be so great... AT FAILING",
    "What you need motivation?\nWHY NOT PUNCHES INSTEAD?!",
    "How in the world did you graduate?",
    "A stone can do much more better than you.",
    "Turn off the PC, go talk to your Senior Dev and admit your mistakes.",
    "Please say sorry to the computer for the things you made it do!",
    "Asse- No. Machine code is more readable than this \"program\" you made.\nCan you even call it one?",
    "Spaghetti.",
    "Go become a chef, you make better spaghetti code than everyone."
]
random.shuffle(messages_bully)

messages_good = [
    "You can do it!",
    "Just a bit more yeah?",
    "Bugs, are bugs...",
    "Bugs? Nah, theyre features now!",
    "It works on my machine.",
    "If it works, it works.",
    "Well slow is better than not working :)",
    "Sometimes you really just\nwanna throw your PC out the window.",
    "There, there, take your time.",
    "Programming is hard, its just like me- I mean relationships.\nYou need to take it slowly and aproach in different angles."
]
random.shuffle(messages_good)


message_good = "Message:\n    "+random.choice(messages_good).replace("\n", "\n  ")
message_bad = "Message >:D\n    "+random.choice(messages_bully).replace("\n", "\n  ")

flags = set()
START = time.time()

MAIN_NAME = "__main__"
SETUP_NAME = "__setup__"