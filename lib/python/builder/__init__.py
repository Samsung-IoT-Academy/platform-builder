import sys

if sys.platform.startswith('linux'):
    from .term import AnsiTerminal as Terminal
elif sys.platform.startswith('win32'):
    from .term import Win32Terminal as Terminal
