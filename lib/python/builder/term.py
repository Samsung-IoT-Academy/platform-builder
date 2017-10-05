from abc import ABCMeta, abstractmethod
import re


def colored(colour, str):
    return "{col}{str}{col}".format(col=colour, str=str)


def success(msg_str):
    return ""


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args,
                                                                 **kwargs)
        return cls._instances[cls]


class Term(ABCMeta):
    def __init__(self):
        # the subclasses declare class attributes which are numbers.
        # Upon instantiation we define instance attributes, which are the same
        # as the class attributes but wrapped with the ANSI escape sequence
        for name in dir(self):
            if not name.startswith('_'):
                value = getattr(self, name)
                setattr(self, name, self.code_to_chars(value))

    @classmethod
    @abstractmethod
    def code_to_chars(cls, code):
        pass

    @classmethod
    @abstractmethod
    def colored(cls, string, color):
        pass


class AnsiTerminal(Term, metaclass=Singleton):
    CSI = '\033['
    COLORS = (
        "black",
        "red",
        "green",
        "yellow",
        "blue",
        "magenta",
        "cyan",
        "white"
        )

    # ----
    # Foreground codes
    # ----
    FG_BLACK = 30
    FG_RED = 31
    FG_GREEN = 32
    FG_YELLOW = 33
    FG_BLUE = 34
    FG_MAGENTA = 35
    FG_CYAN = 36
    FG_WHITE = 37
    # These are fairly well supported, but not part of the standard.
    FG_LIGHT_BLACK = 90
    FG_LIGHT_RED = 91
    FG_LIGHT_GREEN = 92
    FG_LIGHT_YELLOW = 93
    FG_LIGHT_BLUE = 94
    FG_LIGHT_MAGENTA = 95
    FG_LIGHT_CYAN = 96
    FG_LIGHT_WHITE = 97
    # Reset
    FG_RESET = 39

    # ----
    # Background codes
    # ----
    BG_BLACK = 40
    BG_RED = 41
    BG_GREEN = 42
    BG_YELLOW = 43
    BG_BLUE = 44
    BG_MAGENTA = 45
    BG_CYAN = 46
    BG_WHITE = 47
    # These are fairly well supported, but not part of the standard.
    BG_LIGHT_BLACK = 100
    BG_LIGHT_RED = 101
    BG_LIGHT_GREEN = 102
    BG_LIGHT_YELLOW = 103
    BG_LIGHT_BLUE = 104
    BG_LIGHT_MAGENTA = 105
    BG_LIGHT_CYAN = 106
    BG_LIGHT_WHITE = 107
    # Reset
    BG_RESET = 49

    # ----
    # Styles
    # ----
    ST_BRIGHT = 1
    ST_DIM = 2
    ST_NORMAL = 22

    RESET_ALL = 0

    @classmethod
    def colored(cls, string, *args, color="white"):
        colors_regex = "(?P<color>{colors})".format(
            colors="|".join(cls.COLORS))
        styles_regex = "(?P<style>light)?"

        re_color_prefixed = re.compile("^({t}{ws}{c})$".format(
            c=colors_regex, t=styles_regex, ws=r"\s*"))
        re_color_postfixed = re.compile("^({c}{ws}{t})$".format(
            c=colors_regex, t=styles_regex, ws=r"\s*"))

        for re_ in [re_color_prefixed, re_color_postfixed]:
            match = re.match(re_, color)
            if match is not None:
                match = match.groupdict()
                break

        try:
            color = "_" + match['color'].upper()
        except AttributeError:
            color = "_" + "RESET"
        try:
            style = "_" + match['style'].upper()
        except AttributeError:
            style = ""

        cls_color = cls.code_to_chars(getattr(cls, "FG" + style + color))
        end_color = cls.code_to_chars(cls.FG_RESET)
        colored_str = "{col}{msg}{end}".format(col=cls_color,
                                               msg=string,
                                               end=end_color)
        for s in args:
            colored_str += s

        return colored_str

    @classmethod
    def code_to_chars(cls, code):
        return cls.CSI + str(code) + 'm'
