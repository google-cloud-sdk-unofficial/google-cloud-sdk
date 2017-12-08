# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Gcloud Interactive Shell."""

from __future__ import unicode_literals

import os
import shlex
import sys

_GCLOUD_PY_DIR = os.path.dirname(__file__)
_THIRD_PARTY_DIR = os.path.join(_GCLOUD_PY_DIR, 'third_party')

if os.path.isdir(_THIRD_PARTY_DIR):
  sys.path.insert(0, _THIRD_PARTY_DIR)

# pylint: disable=g-import-not-at-top
from googlecloudsdk.command_lib.static_completion import lookup
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log

from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer
from prompt_toolkit.completion import Completion
from prompt_toolkit.history import InMemoryHistory
from pygments.lexers.shell import BashLexer
from pygments.style import Style
from pygments.styles.default import DefaultStyle
from pygments.token import Token


class DocumentStyle(Style):
  styles = {
      Token.Menu.Completions.Completion.Current: '#000000 bg:#00aaaa',
      Token.Menu.Completions.Completion: '#000000 bg:#00ffff',
      Token.Toolbar: '#00ffff bg:#000000'
  }
  styles.update(DefaultStyle.styles)


class ShellCliCompleter(Completer):
  """A prompt_toolkit shell CLI completer."""

  def __init__(self):
    self.table = lookup.LoadTable(_GCLOUD_PY_DIR)

  def get_completions(self, doc, complete_event):
    """Get the completions for doc.

    Args:
      doc: A Document instance containing the shell command line to complete.
      complete_event: The CompleteEvent that triggered this completion.
    Yields:
      List of completions for a given input
    """
    input_line = doc.current_line_before_cursor
    # Make sure first word is gcloud
    if not input_line.split() or input_line.split()[0] != 'gcloud':
      return
    possible_completions = []
    try:
      possible_completions = lookup.FindCompletions(self.table, input_line)
    except lookup.CannotHandleCompletionError:
      return

    for item in possible_completions:
      last = input_line.split(' ')[-1]
      token = 0 - len(last)
      yield Completion(item, token)


def get_bottom_toolbar_tokens(unused_cli):
  return [(Token.Toolbar, ' Gcloud Interactive Shell')]


def run_command(command):
  """Executes command.

  Args:
    command: The command to be executed.
  """
  if not command.split():
    return
  try:
    args = shlex.split(command)
  except ValueError:
    return
  try:
    execution_utils.Exec(args, no_exit=True)
  except execution_utils.InvalidCommandError as err:
    log.err.Print(err)
  except KeyboardInterrupt:
    pass


def main():
  completer = ShellCliCompleter()
  history = InMemoryHistory()
  auto_suggest = AutoSuggestFromHistory()

  while True:
    try:
      command = prompt('$ ', lexer=BashLexer, completer=completer,
                       style=DocumentStyle, history=history,
                       auto_suggest=auto_suggest,
                       get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
                       mouse_support=True)
    except EOFError:
      break
    except KeyboardInterrupt:
      print 'Keyboard Interrupt'
      break
    run_command(command)


if __name__ == '__main__':
  main()
