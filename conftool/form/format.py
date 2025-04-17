class Color:
    BG_RED = '\x1b[41m'
    FG_BOLD_RED = '\x1b[1;31m'

    FG_BOLD_WHITE = '\x1b[1;37m'

    BG_BLUE = '\x1b[44m'

    BG_YELLOW = '\x1b[43m'

    FG_BOLD_BLACK = '\x1b[1;30m'

    FG_BOLD_GREEN = '\x1b[1;32m'

    RESET = '\x1b[0m'

def print_title(msg: str):
    print(Color.BG_RED + Color.FG_BOLD_WHITE + ' ' + msg + ' ' + Color.RESET + '\n')

def print_statement(msg: str):
    print(Color.BG_BLUE + Color.FG_BOLD_WHITE + msg + Color.RESET + "\n")

def print_warning(msg: str):
    print(Color.BG_YELLOW + Color.FG_BOLD_BLACK + "!! " + msg + " !!" + Color.RESET + "\n")

def print_fail(msg: str):
    print(Color.FG_BOLD_RED + ' FAILED: ' + msg + Color.RESET)

def print_ok(msg: str):
    print(Color.FG_BOLD_GREEN + msg + Color.RESET)