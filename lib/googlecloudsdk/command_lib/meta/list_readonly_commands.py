# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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

"""Utilities and CLI tree walker for listing read-only commands."""

import sys

from googlecloudsdk.calliope import walker


def NormalizeRestrict(restrict, top_name='gcloud'):
  """Normalizes command restriction paths for CLI tree walking.

  Args:
    restrict: [str] | None, Dotted or space-separated command path prefixes.
    top_name: str, The root CLI name (defaults to 'gcloud').

  Returns:
    [str] | None, Normalized list of dotted command paths prefixed with
    top_name.
  """
  if not restrict:
    return restrict
  normalized = []
  for item in restrict:
    cleaned = '.'.join(item.strip('. ').split()).replace('_', '-')
    cleaned = '.'.join(part for part in cleaned.split('.') if part)
    if not cleaned:
      continue
    if not cleaned.startswith(f'{top_name}.') and cleaned != top_name:
      cleaned = f'{top_name}.{cleaned}'
    normalized.append(cleaned)
  if not normalized:
    return [f'{top_name}.__empty__']
  return normalized


_NormalizeRestrict = NormalizeRestrict


def DisplayReadOnlyCommands(commands, out=None):
  """Displays the read-only commands on out progressively as they are yielded.

  Args:
    commands: [str] | iterable, The list or generator of command strings.
    out: stream, The output stream, sys.stdout if None.
  """
  if not out:
    out = sys.stdout
  if commands:
    for cmd in commands:
      out.write(f'{cmd}\n')
      out.flush()


class ReadOnlyCommandWalker(walker.Walker):
  """Walker that inspects command metadata for read_only flags.

  Attributes:
    commands: [str], The collected space-separated command paths matching the
      configured state.
  """

  def __init__(self, cli, restrict=None, state='readonly'):
    """Initializes the walker.

    Args:
      cli: The Calliope CLI object to traverse.
      restrict: [str] | None, Dotted command/group path prefixes to include.
      state: str, Target read_only state ('readonly', 'mutating', or
        'unannotated').
    """
    self._cli = cli
    self._top_name = getattr(cli, 'name', 'gcloud')
    restrict = NormalizeRestrict(restrict, top_name=self._top_name)
    self._init_restrict = restrict
    super().__init__(cli, ignore_load_errors=True, restrict=restrict)
    self.commands = []
    self._state = state

  def _GetReadOnlyState(self, node):
    """Returns 'readonly', 'mutating', or 'unannotated' for a command node."""
    hints = getattr(node, 'hints', None)
    read_only_hint = getattr(hints, 'read_only', None)
    if isinstance(read_only_hint, bool):
      return 'readonly' if read_only_hint else 'mutating'
    return 'unannotated'

  def _MatchesState(self, node):
    """Returns True if the command node matches the target read_only state."""
    return self._GetReadOnlyState(node) == self._state

  def _IsReadOnly(self, node):
    """Returns True if node matches the configured state."""
    return self._MatchesState(node)

  def Visit(self, node, parent, is_group):
    """Visits each node in the CLI command tree.

    Args:
      node: CommandCommon tree node.
      parent: The parent Visit() return value, unused here.
      is_group: True if node is a group, otherwise it is a command.

    Returns:
      The parent arg for the Visit() calls for the children of this node.
    """
    if not is_group and self._MatchesState(node):
      self.commands.append(' '.join(node.GetPath()))
    return parent

  def Walk(self, hidden=False, universe_compatible=False, restrict=None):
    """Yields matching command paths progressively as the CLI tree is scanned.

    Args:
      hidden: Include hidden groups and commands if True.
      universe_compatible: Exclusively include universe compatible commands.
      restrict: Restricts the walk to the command/group dotted paths.

    Yields:
      str, The space-separated matching command paths in DFS order.
    """
    if restrict is not None:
      restrict = NormalizeRestrict(restrict, top_name=self._top_name)

    def _IsUniverseCompatible(command):
      return not isinstance(command, dict) and command.IsUniverseCompatible()

    def _Include(command, traverse=False):
      if not hidden and command.IsHidden():
        return False
      if universe_compatible and not _IsUniverseCompatible(command):
        return False
      if not restrict:
        return True
      path = '.'.join(command.GetPath())
      for item in restrict:
        if path == item or path.startswith(f'{item}.'):
          return True
        if traverse and (item == path or item.startswith(f'{path}.')):
          return True
      return False

    seen = set()

    def _VisitLeaf(command, parent):
      prev_len = len(self.commands)
      self._Visit(command, parent, is_group=False)
      if len(self.commands) > prev_len:
        cmd_path = self.commands[-1]
        if cmd_path not in seen:
          seen.add(cmd_path)
          yield cmd_path
        else:
          self.commands.pop()

    def _Walk(node, parent):
      if not node.is_group:
        if _Include(node):
          yield from _VisitLeaf(node, parent)
        return

      if not _Include(node, traverse=True):
        return

      parent = self._Visit(node, parent, is_group=True)
      commands_and_groups = []

      if node.commands:
        for name, command in sorted(node.commands.items()):
          if _Include(command):
            commands_and_groups.append((name, command, False))
      if node.groups:
        for name, command in sorted(node.groups.items()):
          if _Include(command, traverse=True):
            commands_and_groups.append((name, command, True))

      for _, command, is_group in sorted(commands_and_groups):
        if is_group:
          yield from _Walk(command, parent)
        else:
          yield from _VisitLeaf(command, parent)

    roots = self._roots
    if (
        restrict is not None
        and getattr(self, '_init_restrict', None) is not None
        and restrict != self._init_restrict
    ):
      top = self._cli._TopElement()  # pylint: disable=protected-access
      resolved = [self._GetSubElement(top, r) for r in restrict]
      roots = [r for r in resolved if r]
      for root in roots:
        root.LoadAllSubElements(recursive=True, ignore_load_errors=True)

    self.commands = []
    self._num_visited = 0
    for root in roots:
      yield from _Walk(root, None)
    self.Done()
