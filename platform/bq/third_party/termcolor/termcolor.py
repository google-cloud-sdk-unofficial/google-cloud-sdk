#!/usr/bin/env python
# Copyright (c) 2008-2011 Volvox Development Team
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Author: Konstantin Lepa <konstantin.lepa@gmail.com>

"""ANSI color formatting for output in terminal."""

from __future__ import annotations

import os
from functools import cache

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any


ATTRIBUTES: dict[str, int] = {
    "bold": 1,
    "dark": 2,
    "italic": 3,
    "underline": 4,
    "blink": 5,
    "reverse": 7,
    "concealed": 8,
    "strike": 9,
}

HIGHLIGHTS: dict[str, int] = {
    "on_black": 40,
    "on_grey": 40,  # Actually black but kept for backwards compatibility
    "on_red": 41,
    "on_green": 42,
    "on_yellow": 43,
    "on_blue": 44,
    "on_magenta": 45,
    "on_cyan": 46,
    "on_light_grey": 47,
    "on_dark_grey": 100,
    "on_light_red": 101,
    "on_light_green": 102,
    "on_light_yellow": 103,
    "on_light_blue": 104,
    "on_light_magenta": 105,
    "on_light_cyan": 106,
    "on_white": 107,
}

COLORS: dict[str, int] = {
    "black": 30,
    "grey": 30,  # Actually black but kept for backwards compatibility
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "light_grey": 37,
    "dark_grey": 90,
    "light_red": 91,
    "light_green": 92,
    "light_yellow": 93,
    "light_blue": 94,
    "light_magenta": 95,
    "light_cyan": 96,
    "white": 97,
}


RESET = "\033[0m"


@cache
def can_colorize(
    *,
    no_color: object = None,  # GOOGLE-LOCAL: upstream type is `bool | None`.
    force_color: object = None,  # GOOGLE-LOCAL: upstream type is `bool | None`.
) -> bool:
    """Check env vars and for tty/dumb terminal"""
    # First check overrides:
    # "User-level configuration files and per-instance command-line arguments should
    # override $NO_COLOR. A user should be able to export $NO_COLOR in their shell
    # configuration file as a default, but configure a specific program in its
    # configuration file to specifically enable color."
    # https://no-color.org
    if no_color is not None and no_color:
        return False
    if force_color is not None and force_color:
        return True

    # Then check env vars:
    if os.environ.get("ANSI_COLORS_DISABLED"):
        return False
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True

    # GOOGLE-LOCAL PATCH -- keep when re-importing from upstream.
    #
    # Upstream (>= 2.1) additionally returns False here when TERM=dumb or when
    # sys.stdout is not a TTY. google3 shipped termcolor 1.1.0 from 2011 until
    # this upgrade, and that version coloured unconditionally unless
    # ANSI_COLORS_DISABLED was set. Tens of thousands of google3 files import
    # termcolor and many tools and tests rely on escape codes being present in
    # piped / captured output (blaze test, logs, subprocess pipes). To keep the
    # upgrade behaviour-preserving we retain the historical default.
    #
    # Callers that want upstream's TTY-aware behaviour can opt in explicitly,
    # e.g. colored(text, "red", no_color=not sys.stdout.isatty()), or set
    # NO_COLOR / ANSI_COLORS_DISABLED in the environment.
    return True


# GOOGLE-LOCAL PATCH -- keep when re-importing from upstream.
#
# Upstream annotates the colour parameters of colored() / cprint() as
# `str | tuple[int, int, int] | None` and the override flags as `bool | None`.
# termcolor 1.1.0, which google3 used from 2011 until this upgrade, was
# unannotated, so existing callers were never type-checked against it and some
# pass values with looser static types (from untyped dicts, `*args` lists,
# logging.LoggerAdapter.extra, ...). With the upstream annotations those
# callers fail Pyrefly and break their builds.
#
# The parameters are annotated as `object` here instead. This matches the
# actual runtime contract of this code: a colour that is neither a known name
# nor an RGB tuple is ignored (upstream's own tests rely on this), and the
# override flags are only tested for truthiness. The intended upstream types
# are noted next to each parameter. Restore the upstream annotations once
# google3 callers pass properly typed values.
def colored(
    text: object,
    color: object = None,  # Upstream: str | tuple[int, int, int] | None
    on_color: object = None,  # Upstream: str | tuple[int, int, int] | None
    attrs: Iterable[str] | None = None,
    *,
    no_color: object = None,  # Upstream: bool | None
    force_color: object = None,  # Upstream: bool | None
) -> str:
    """Colorize text.

    Available text colors:
        black, red, green, yellow, blue, magenta, cyan, white,
        light_grey, dark_grey, light_red, light_green, light_yellow, light_blue,
        light_magenta, light_cyan.

    Available text highlights:
        on_black, on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_white,
        on_light_grey, on_dark_grey, on_light_red, on_light_green, on_light_yellow,
        on_light_blue, on_light_magenta, on_light_cyan.

    Alternatively, both text colors (color) and highlights (on_color) may
    be specified via a tuple of 0-255 ints (R, G, B).

    Available attributes:
        bold, dark, italic, underline, blink, reverse, concealed, strike.

    Example:
        colored('Hello, World!', 'red', 'on_black', ['bold', 'blink'])
        colored('Hello, World!', 'green')
        colored('Hello, World!', (255, 0, 255))  # Purple
    """
    result = str(text)
    if not can_colorize(no_color=no_color, force_color=force_color):
        return result

    fmt_str = "\033[%dm%s"
    rgb_fore_fmt_str = "\033[38;2;%d;%d;%dm%s"
    rgb_back_fmt_str = "\033[48;2;%d;%d;%dm%s"
    if color is not None:
        if isinstance(color, str):
            result = fmt_str % (COLORS[color], result)
        elif isinstance(color, tuple):
            result = rgb_fore_fmt_str % (color[0], color[1], color[2], result)

    if on_color is not None:
        if isinstance(on_color, str):
            result = fmt_str % (HIGHLIGHTS[on_color], result)
        elif isinstance(on_color, tuple):
            result = rgb_back_fmt_str % (on_color[0], on_color[1], on_color[2], result)

    if attrs is not None:
        for attr in attrs:
            result = fmt_str % (ATTRIBUTES[attr], result)

    result += RESET

    return result


def cprint(
    text: object,
    color: object = None,  # GOOGLE-LOCAL (see colored()): upstream str | tuple | None
    on_color: object = None,  # GOOGLE-LOCAL (see colored()): upstream str | tuple | None
    attrs: Iterable[str] | None = None,
    *,
    no_color: object = None,  # GOOGLE-LOCAL (see colored()): upstream bool | None
    force_color: object = None,  # GOOGLE-LOCAL (see colored()): upstream bool | None
    **kwargs: Any,
) -> None:
    """Print colorized text.

    It accepts arguments of print function.
    """

    print(
        (
            colored(
                text,
                color,
                on_color,
                attrs,
                no_color=no_color,
                force_color=force_color,
            )
        ),
        **kwargs,
    )
