#!/usr/bin/env python
# Copyright 2017 The Abseil Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generic entry point for Abseil Python applications.

To use this module, define a ``main`` function with a single ``argv`` argument
and call ``app.run(main)``. For example::

    def main(argv):
      if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')

    if __name__ == '__main__':
      app.run(main)
"""

import collections
import errno
import importlib
import os
import pdb
import sys
import textwrap
import traceback

from absl import command_name
from absl import flags
from absl import logging

# absl:google3-begin(Google3 modules)
# pylint: disable=g-import-not-at-top
from pyglib import build_data
from pyglib import toollog
# absl:google3-end
try:
  import faulthandler
except ImportError:
  faulthandler = None
# absl:google3-begin(absl_faulthandler is google3 module)
else:
  try:
    from google.base.python import absl_faulthandler
  except ImportError:
    pass
  else:
    if not faulthandler.is_enabled():
      faulthandler.preserve_existing_handlers()
      absl_faulthandler.register_fatal_error_handler(
          faulthandler.sigsafe_traceback_capsule()
      )
# pylint: enable=g-import-not-at-top
# absl:google3-end

FLAGS = flags.FLAGS

RUN_WITH_PDB = flags.DEFINE_boolean(
    'run_with_pdb',
    False,
    'Set to true for debug mode. PDB is used by default; $PYTHONBREAKPOINT '
    '(https://docs.python.org/3/using/cmdline.html#envvar-PYTHONBREAKPOINT) '
    'can be used to specify a custom debugger.',
)
PDB_POST_MORTEM = flags.DEFINE_boolean(
    'pdb_post_mortem',
    False,
    'Set to true to handle uncaught exceptions with the post mortem debugger. '
    'PDB is used by default; $PYTHONBREAKPOINT '
    '(https://docs.python.org/3/using/cmdline.html#envvar-PYTHONBREAKPOINT) '
    'can be used to specify a custom one.',
)
PDB = flags.DEFINE_alias('pdb', 'pdb_post_mortem')
RUN_WITH_PROFILING = flags.DEFINE_boolean(
    'run_with_profiling',
    False,
    'Set to true for profiling the script. '
    'Execution will be slower, and the output format might '
    'change over time.',
)
PROFILE_FILE = flags.DEFINE_string(
    'profile_file',
    os.getenv('ABSL_PYTHON_PROFILE_FILE'),
    'Dump profile information to a file (for python -m '
    'pstats). Implies --run_with_profiling.',
)
USE_CPROFILE_FOR_PROFILING = flags.DEFINE_boolean(
    'use_cprofile_for_profiling',
    True,
    'Use cProfile instead of the profile module for '
    'profiling. This has no effect unless '
    '--run_with_profiling is set.',
)
# absl:google3-begin(Support for profilez)
# TODO: b/7623388 - Finish implementing this and turn it on by default.
_ENABLE_PYTHON_PROFILEZ = flags.DEFINE_boolean(
    'enable_python_profilez', False, 'do not use - under development'
)

# absl:google3-end
_ONLY_CHECK_ARGS = flags.DEFINE_boolean(
    'only_check_args',
    False,
    'Set to true to validate args and exit.',
    allow_hide_cpp=True,
)

# absl:google3-begin(Only applies to C++ integration, not released yet)

# Try to import pywrapbase and _cpp_flags.  It may fail if the
# original BUILD file did not list it as a dependency, in which case
# we can't use_cpp_logging.  This is a best-effort approach.  If
# pywrapbase can't be imported, we'll do without C++ support.
# pylint: disable=g-import-not-at-top
try:
  from absl.flags import _cpp_flags
  from google.base.python import pywrapbase
except ImportError:
  pywrapbase = None

try:
  from google.base.python.clif import googleinit
except ImportError:
  assert (
      not pywrapbase
  ), 'googleinit should be available with //base/python:pywrapbase'
  googleinit = None

try:
  from google.devtools.python.profiler import pywrapprofilezgoogle3
except ImportError:
  pywrapprofilezgoogle3 = None


# pylint: enable=g-import-not-at-top
# absl:google3-end
# absl:google3-begin(googletest)
def _prevent_googletest_error_on_exit() -> None:
  """Prevent googletest from raising an error when exiting runtime.

  If googletest is imported, it requires `googletest.main()` to be called or it
  will raise an error. This will ensure an error won't be raised so that runtime
  can safely exit.
  """

  googletest = sys.modules.get('google3.testing.pybase.googletest')
  if googletest:
    googletest.ThisTestIsUsefulWithoutCallingMain()  # pytype: disable=attribute-error


# absl:google3-end


def _exit_before_main(status_code) -> None:
  """Abstraction of exiting before main() to enable overrides."""
  # absl:google3-begin(googletest)
  # Preventing an error about googletest.main() not being called because we are
  # intentionally exiting early.
  _prevent_googletest_error_on_exit()
  # absl:google3-end
  sys.exit(status_code)


def _get_debugger_module_with_function(function_name):
  """Provides the `$PYTHONBREAKPOINT` module if it contains `function_name`.

  Falls back to `pdb` otherwise.

  Args:
    function_name: The name of the function required.

  Returns:
    A debugger module providing `function_name`.
  """
  python_breakpoint = os.getenv('PYTHONBREAKPOINT')
  # The special value '0' for `$PYTHONBREAKPOINT` means "do not use a debugger".
  # We don't respect it (if the user explicitly asks to debug) but shouldn't try
  # to import a module with this name.
  if python_breakpoint and python_breakpoint != '0':
    debugger_module_import = python_breakpoint.rsplit('.', 1)[0]
    try:
      debugger_module = importlib.import_module(debugger_module_import)
    except ImportError:
      logging.warning(
          (
              'Could not import $PYTHONBREAKPOINT debugger module %r, '
              'falling back to PDB'
              # absl:google3-begin(Mentions Blaze, only applies to google3)
              '. Perhaps you would like to pass '
              '--//tools/python:debugger=//third_party/py/... to Blaze '
              'or add it to your .blazerc (go/blazerc)?'
              # absl:google3-end
          ),
          debugger_module_import,
      )
    else:
      if hasattr(debugger_module, function_name):
        return debugger_module
      logging.warning(
          '$PYTHONBREAKPOINT debugger %r has no function %r, '
          'falling back to PDB',
          debugger_module_import,
          function_name,
      )
  return pdb


# If main() exits via an abnormal exception, call into these
# handlers before exiting.
EXCEPTION_HANDLERS = []


class Error(Exception):
  pass


class UsageError(Error):
  """Exception raised when the arguments supplied by the user are invalid.

  Raise this when the arguments supplied are invalid from the point of
  view of the application. For example when two mutually exclusive
  flags have been supplied or when there are not enough non-flag
  arguments. It is distinct from flags.Error which covers the lower
  level of parsing and validating individual flags.
  """

  def __init__(self, message, exitcode=1):
    super().__init__(message)
    self.exitcode = exitcode


class HelpFlag(flags.BooleanFlag):
  """Special boolean flag that displays usage and raises SystemExit."""

  NAME = 'help'
  SHORT_NAME = '?'

  def __init__(self):
    super().__init__(
        self.NAME,
        False,
        'show this help',
        short_name=self.SHORT_NAME,
        allow_hide_cpp=True,
    )

  def parse(self, arg):
    if self._parse(arg):
      usage(shorthelp=True, writeto_stdout=True)
      # Advertise --helpfull on stdout, since usage() was on stdout.
      print()
      print('Try --helpfull to get a list of all flags.')
      _exit_before_main(1)


class HelpshortFlag(HelpFlag):
  """--helpshort is an alias for --help."""

  NAME = 'helpshort'
  SHORT_NAME = None


class HelpfullFlag(flags.BooleanFlag):
  """Display help for flags in the main module and all dependent modules."""

  def __init__(self):
    super().__init__('helpfull', False, 'show full help', allow_hide_cpp=True)

  def parse(self, arg):
    if self._parse(arg):
      usage(writeto_stdout=True)
      _exit_before_main(1)


class HelpXMLFlag(flags.BooleanFlag):
  """Similar to HelpfullFlag, but generates output in XML format."""

  def __init__(self):
    super().__init__(
        'helpxml',
        False,
        'like --helpfull, but generates XML output',
        allow_hide_cpp=True,
    )

  def parse(self, arg):
    if self._parse(arg):
      flags.FLAGS.write_help_in_xml_format(sys.stdout)
      _exit_before_main(1)


class OnlyCheckFlagsFlag(flags.BooleanFlag):
  """Similar to HelpFlag, but only checks flag definitions.

  In the process it will load all modules defining flags and verify there are no
  duplicate flag definitions.
  """

  def __init__(self):
    super().__init__(
        'only_check_flags',
        False,
        'Check if all flag definitions are valid and exit before main.',
        allow_hide_cpp=True,
    )

  def parse(self, arg):
    if self._parse(arg):
      # absl:google3-begin(go/py-lazy-imports)
      FLAGS._force_discover_all_flags()  # pylint: disable=protected-access
      # absl:google3-end
      sys.stdout.write('SUCCESS: All Abseil flags are valid.\n')
      _exit_before_main(0)


# absl:google3-begin(--show_build_data only defined in google3)
class BuildDataFlag(flags.BooleanFlag):
  """Boolean flag that writes build data to stdout and exits."""

  def __init__(self, flag_name='show_build_data', allow_override_cpp=False):
    super().__init__(
        flag_name,
        False,
        'show build data and exit',
        allow_override_cpp=allow_override_cpp,
    )

  def parse(self, arg):
    if self._parse(arg):
      sys.stdout.write(build_data.BuildData())
      _exit_before_main(0)


# absl:google3-end
def parse_flags_with_usage(args):
  """Tries to parse the flags, print usage, and exit if unparsable.

  Args:
    args: [str], a non-empty list of the command line arguments including
      program name.

  Returns:
    [str], a non-empty list of remaining command line arguments after parsing
    flags, including program name.
  """
  try:
    return FLAGS(args)
  except flags.Error as error:
    message = str(error)
    if '\n' in message:
      message = textwrap.indent(message, '  ')
      final_message = f'FATAL Flags parsing error:\n{message}\n'
    else:
      final_message = f'FATAL Flags parsing error: {message}\n'
    sys.stderr.write(final_message)
    # absl:google3-begin(Google-only function)
    logging.gwq_status_message(final_message)
    # absl:google3-end
    sys.stderr.write('Pass --helpshort or --helpfull to see help on flags.\n')
    _exit_before_main(1)


_define_help_flags_called = False


def define_help_flags():
  """Registers help flags. Idempotent."""
  # Use a global to ensure idempotence.
  global _define_help_flags_called

  if not _define_help_flags_called:
    flags.DEFINE_flag(HelpFlag())
    flags.DEFINE_flag(HelpshortFlag())  # alias for --help
    flags.DEFINE_flag(HelpfullFlag())
    flags.DEFINE_flag(HelpXMLFlag())
    flags.DEFINE_flag(OnlyCheckFlagsFlag())
    # absl:google3-begin(--show_build_data only defined in google3)
    flags.DEFINE_flag(BuildDataFlag())
    if 'version' not in flags.FLAGS:
      # b/133872520 -- create '--version' as alias for '--show_build_data'
      # C++ may override this flag.
      flags.DEFINE_flag(BuildDataFlag('version', allow_override_cpp=True))
    # absl:google3-end
    _define_help_flags_called = True


# absl:google3-begin(Only applies to C++ integration, not released yet)
def _log_process_info():
  """Logs this process's commandline and build information.

  The format imitates the C++ logs from InitGoogle.
  """
  logging.info('Process id %s', os.getpid())
  try:
    logging.info('Current working directory %s', os.getcwd())
  except OSError as e:
    logging.info('Error trying to get working directory: %s', e)
  logging.info(build_data.BuildData())
  if googleinit is not None and not googleinit.IsNDebugDefined():
    logging.warning('DEBUG BINARY -- Performance may suffer')
  logging.info('Command line arguments:')
  for i, arg in enumerate(sys.argv):
    logging.info("argv[%s]: '%s'", i, arg)


# absl:google3-end
def _register_and_parse_flags_with_usage(
    argv=None,
    flags_parser=parse_flags_with_usage,
    # absl:google3-begin(Only applies to C++ integration, not released yet)
    change_root_and_user=True,
    # absl:google3-end
):
  # absl:google3-begin(For lint)
  # The scrubbing comments mess up the doc args lint check.
  # pylint: disable=g-doc-args
  # fmt: off
  # absl:google3-end
  """Registers help flags, parses arguments and shows usage if appropriate.

  This also calls sys.exit(0) if flag --only_check_args is True.

  # absl:google3-begin(Only applies to C++ integration, not released yet)
  This also takes care of C++ GoogleInit for ABSL library initialization.

  # absl:google3-end
  Args:
    argv: [str], a non-empty list of the command line arguments including
      program name, sys.argv is used if None.
    flags_parser: Callable[[List[str]], Any], the function used to parse flags.
      The return value of this function is passed to `main` untouched. It must
      guarantee FLAGS is parsed after this function is called.
    # absl:google3-begin(Only applies to C++ integration, not released yet)
    change_root_and_user: If False, use InitGoogleExceptChangeRootAndUserScript.
    # absl:google3-end

  Returns:
    The return value of `flags_parser`. When using the default `flags_parser`,
    it returns the following:
    [str], a non-empty list of remaining command line arguments after parsing
    flags, including program name.

  Raises:
    Error: Raised when flags_parser is called, but FLAGS is not parsed.
    SystemError: Raised when it's called more than once.
  """
  # fmt: on
  if _register_and_parse_flags_with_usage.done:
    raise SystemError('Flag registration can be done only once.')

  define_help_flags()

  original_argv = sys.argv if argv is None else argv
  # absl:google3-begin(Only applies to C++ integration, not released yet)
  cpp_flag_objects = _cpp_flags.load() if pywrapbase else []
  # absl:google3-end
  args_to_main = flags_parser(original_argv)
  if not FLAGS.is_parsed():
    raise Error('FLAGS must be parsed after flags_parser is called.')

  # Exit when told so.
  if _ONLY_CHECK_ARGS.value:
    _exit_before_main(0)
  # Immediately after flags are parsed, bump verbosity to INFO if the flag has
  # not been set.
  if FLAGS['verbosity'].using_default_value:
    FLAGS.verbosity = 0
  # absl:google3-begin(Only applies to C++ integration, not released yet)

  # C++ InitGoogle sets --silent_init to false before it returns, so it must
  # be read before calling InitGoogle.
  silent_init = FLAGS.silent_init if pywrapbase else True

  if googleinit:
    cargs = original_argv[:1]
    if pywrapbase:
      _cpp_flags.set_argv(original_argv)
      cargs += _cpp_flags.get_cpp_args(cpp_flag_objects)
    googleinit.Run(cargs, change_root_and_user=change_root_and_user)
    if pywrapbase:
      _cpp_flags.synchronize_cpp_flags(cpp_flag_objects)
  if pywrapbase:
    logging.use_cpp_logging()

  if not silent_init:
    _log_process_info()

  if pywrapprofilezgoogle3 and _ENABLE_PYTHON_PROFILEZ.value:
    pywrapprofilezgoogle3.PythonProfilezGoogle3.RegisterPythonProfilezHandler()
  # absl:google3-end
  _register_and_parse_flags_with_usage.done = True

  return args_to_main


_register_and_parse_flags_with_usage.done = False


def _run_main(main, argv):
  """Calls main, optionally with a debugger or profiler."""
  if RUN_WITH_PDB.value:
    sys.exit(_get_debugger_module_with_function('runcall').runcall(main, argv))
  elif RUN_WITH_PROFILING.value or PROFILE_FILE.value:
    # Avoid import overhead since most apps (including performance-sensitive
    # ones) won't be run with profiling.
    # pylint: disable=g-import-not-at-top
    import atexit

    if USE_CPROFILE_FOR_PROFILING.value:
      import cProfile as profile
    else:
      import profile
    profiler = profile.Profile()
    if PROFILE_FILE.value:
      atexit.register(profiler.dump_stats, PROFILE_FILE.value)
    else:
      atexit.register(profiler.print_stats)
    sys.exit(profiler.runcall(main, argv))
  else:
    sys.exit(main(argv))


def _call_exception_handlers(exception):
  """Calls any installed exception handlers."""
  for handler in EXCEPTION_HANDLERS:
    try:
      if handler.wants(exception):
        handler.handle(exception)
    except:  # pylint: disable=bare-except
      try:
        # We don't want to stop for exceptions in the exception handlers but
        # we shouldn't hide them either.
        logging.error(traceback.format_exc())
      except:  # pylint: disable=bare-except
        # In case even the logging statement fails, ignore.
        pass


# absl:google3-begin(change_root_and_user is used with C++, not released yet)
# TODO(b/31437489): Use **kwargs for flags_parser and change_root_and_user.
# absl:google3-end
def run(
    main,
    argv=None,
    flags_parser=parse_flags_with_usage,
    # absl:google3-begin(Used with C++, not released yet)
    change_root_and_user=True,
    # absl:google3-end
):
  # absl:google3-begin(For lint)
  # The copybara markers mess up the doc args lint check.
  # pylint: disable=g-doc-args
  # fmt: off
  # absl:google3-end
  """Begins executing the program.

  Args:
    main: The main function to execute. It takes an single argument "argv",
        which is a list of command line arguments with parsed flags removed.
        The return value is passed to `sys.exit`, and so for example
        a return value of 0 or None results in a successful termination, whereas
        a return value of 1 results in abnormal termination.
        For more details, see https://docs.python.org/3/library/sys#sys.exit
    argv: A non-empty list of the command line arguments including program name,
        sys.argv is used if None.
    flags_parser: Callable[[List[str]], Any], the function used to parse flags.
        The return value of this function is passed to `main` untouched.
        It must guarantee FLAGS is parsed after this function is called.
        Should be passed as a keyword-only arg which will become mandatory in a
        future release.
    # absl:google3-begin(Not released yet)
    change_root_and_user: Allow the C++ InitGoogle call to obey the --chroot
        --uid, and --gid flags.  Defaults to True.  The only code likely to
        want to pass False is code intended to be run as root.  Prefer using
        this parameter rather than calling flags.SetChangeRootAndUser(False).
        Should be passed as a keyword-only arg which will become mandatory in a
        future release.
     - loads C++ flags
     - calls InitGoogle
     - calls use_cpp_logging
    # absl:google3-end
  - Parses command line flags with the flag module.
  - If there are any errors, prints usage().
  - Calls main() with the remaining arguments.
  - If main() raises a UsageError, prints usage and the error message.
  """
  # fmt: on
  try:
    args = _run_init(
        sys.argv if argv is None else argv,
        flags_parser,
        # absl:google3-begin(Used with C++, not released yet)
        change_root_and_user,
        # absl:google3-end
    )
    while _init_callbacks:
      callback = _init_callbacks.popleft()
      callback()
    try:
      _run_main(main, args)
    except UsageError as error:
      usage(shorthelp=True, detailed_error=error, exitcode=error.exitcode)
    except:
      exc = sys.exc_info()[1]
      # Don't try to post-mortem debug successful SystemExits, since those
      # mean there wasn't actually an error. In particular, the test framework
      # raises SystemExit(False) even if all tests passed.
      if isinstance(exc, SystemExit) and not exc.code:
        raise

      # Check the tty so that we don't hang waiting for input in an
      # non-interactive scenario.
      if PDB_POST_MORTEM.value and sys.stdout.isatty():
        traceback.print_exc()
        print()
        print(' *** Entering post-mortem debugging ***')
        print()
        _get_debugger_module_with_function('post_mortem').post_mortem()
      raise
  except Exception as e:
    _call_exception_handlers(e)
    raise


# Callbacks which have been deferred until after _run_init has been called.
_init_callbacks = collections.deque()


def call_after_init(callback):
  """Calls the given callback only once ABSL has finished initialization.

  If ABSL has already finished initialization when ``call_after_init`` is
  called then the callback is executed immediately, otherwise `callback` is
  stored to be executed after ``app.run`` has finished initializing (aka. just
  before the main function is called).

  If called after ``app.run``, this is equivalent to calling ``callback()`` in
  the caller thread. If called before ``app.run``, callbacks are run
  sequentially (in an undefined order) in the same thread as ``app.run``.

  Args:
    callback: a callable to be called once ABSL has finished initialization.
      This may be immediate if initialization has already finished. It takes no
      arguments and returns nothing.
  """
  if _run_init.done:
    callback()
  else:
    _init_callbacks.append(callback)


def _run_init(
    argv,
    flags_parser,
    # absl:google3-begin(Used with C++, not released yet)
    change_root_and_user,
    # absl:google3-end
):
  """Does one-time initialization and re-parses flags on rerun."""
  if _run_init.done:
    return flags_parser(argv)
  command_name.make_process_name_useful()
  # Set up absl logging handler.
  logging.use_absl_handler()
  args = _register_and_parse_flags_with_usage(
      argv=argv,
      flags_parser=flags_parser,
      # absl:google3-begin(Only applies to C++ integration, not released yet)
      change_root_and_user=change_root_and_user,
      # absl:google3-end
  )
  # absl:google3-begin(toollog is google3 module)
  if toollog is not None:
    toollog.MaybeSyslogOnStart()
  # absl:google3-end
  # absl:google3-begin(Only applies to C++ integration, not released yet)
  # After InitGoogle (done by ParseFlags), for chaining with the C++ handler.
  # absl:google3-end
  if faulthandler:
    try:
      faulthandler.enable()
    except Exception:  # pylint: disable=broad-except
      # Some tests verify stderr output very closely, so don't print anything.
      # Disabled faulthandler is a low-impact error.
      pass
  _run_init.done = True
  return args


_run_init.done = False


def usage(
    shorthelp=False, writeto_stdout=False, detailed_error=None, exitcode=None
):
  """Writes __main__'s docstring to stderr with some help text.

  Args:
    shorthelp: bool, if True, prints only flags from the main module, rather
      than all flags.
    writeto_stdout: bool, if True, writes help message to stdout, rather than to
      stderr.
    detailed_error: str, additional detail about why usage info was presented.
    exitcode: optional integer, if set, exits with this status code after
      writing help.
  """
  if writeto_stdout:
    stdfile = sys.stdout
  else:
    stdfile = sys.stderr

  doc = sys.modules['__main__'].__doc__
  if not doc:
    doc = f'\nUSAGE: {sys.argv[0]} [flags]\n'
    doc = flags.text_wrap(doc, indent='       ', firstline_indent='')
  else:
    # Replace all '%s' with sys.argv[0], and all '%%' with '%'.
    num_specifiers = doc.count('%') - 2 * doc.count('%%')
    try:
      doc %= (sys.argv[0],) * num_specifiers
    except (OverflowError, TypeError, ValueError):
      # Just display the docstring as-is.
      pass
  if shorthelp:
    flag_str = FLAGS.main_module_help()
  else:
    flag_str = FLAGS.get_help()
  try:
    stdfile.write(doc)
    if flag_str:
      stdfile.write('\nflags:\n')
      stdfile.write(flag_str)
    stdfile.write('\n')
    if detailed_error is not None:
      stdfile.write(f'\n{detailed_error}\n')
  except OSError as e:
    # We avoid printing a huge backtrace if we get EPIPE, because
    # "foo.par --help | less" is a frequent use case.
    if e.errno != errno.EPIPE:
      raise
  if exitcode is not None:
    sys.exit(exitcode)


class ExceptionHandler:
  """Base exception handler from which other may inherit."""

  def wants(self, exc):
    """Returns whether this handler wants to handle the exception or not.

    This base class returns True for all exceptions by default. Override in
    subclass if it wants to be more selective.

    Args:
      exc: Exception, the current exception.
    """
    del exc  # Unused.
    return True

  def handle(self, exc):
    """Do something with the current exception.

    Args:
      exc: Exception, the current exception

    This method must be overridden.
    """
    raise NotImplementedError()


def install_exception_handler(handler):
  """Installs an exception handler.

  Args:
    handler: ExceptionHandler, the exception handler to install.

  Raises:
    TypeError: Raised when the handler was not of the correct type.

  All installed exception handlers will be called if main() exits via
  an abnormal exception, i.e. not one of SystemExit, KeyboardInterrupt,
  FlagsError or UsageError.
  """
  if not isinstance(handler, ExceptionHandler):
    raise TypeError(
        f'handler of type {type(handler)} does not inherit from'
        ' ExceptionHandler'
    )
  EXCEPTION_HANDLERS.append(handler)


# absl:google3-begin(Only applies to C++ integration, not released yet)


class _CppLoggingExceptionHandler(ExceptionHandler):
  """If we are using C++ logging, log the exception to INFO log."""

  def handle(self, exc):
    """Handle the exception."""
    if logging.is_using_cpp_logging():
      logging.error('Top-level exception: %s', exc)
      logging.error(''.join(traceback.format_exception(*sys.exc_info())))
      logging.gwq_status_message(f'{type(exc).__name__}: {exc}')


install_exception_handler(_CppLoggingExceptionHandler())
# absl:google3-end
