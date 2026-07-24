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
"""Provides a parser for Pub/Sub scaling arguments."""

from __future__ import annotations

import collections
from collections.abc import Sequence
import re
from typing import Any

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import cli
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.run import flags


def PubSubScalingArgGroup() -> calliope_base.ArgumentGroup:
  """Returns an argument group with per-subscription Pub/Sub scaling args."""
  group = calliope_base.ArgumentGroup(help='Pub/Sub Scaling Flags', hidden=True)
  group.AddArgument(flags.PubsubSubscriptionFlag())
  group.AddArgument(flags.PubsubTargetFlag())
  return group


def AddPubSubScalingFlags(
    parser: parser_arguments.ArgumentInterceptor,
    release_track=calliope_base.ReleaseTrack.GA,
):
  """AddPubSubScalingFlags updates parser to add Pub/Sub scaling arg parsing.

  Args:
    parser: The parser to patch.
    release_track: The release track of the command.
  """
  group = PubSubScalingArgGroup()
  group.AddToParser(parser)

  pubsub_parser = PubSubScalingParser(
      parser.parser, group, release_track
  )
  parser.parser.parse_known_args = pubsub_parser.ParseKnownArgs


class PubSubScalingParser(object):
  """PubSubScalingParser adds custom Pub/Sub scaling parsing behavior to ArgumentParser."""

  _SUBSCRIPTION_FLAG_NAME = '--scaling-pubsub-subscription'
  _FLAG_PATTERN = r'^(--[^:=]+)[:=]?.*'

  def __init__(
      self,
      parser: parser_extensions.ArgumentParser,
      pubsub_arg_group: calliope_base.ArgumentGroup,
      release_track: calliope_base.ReleaseTrack,
  ):
    """PubSubScalingParser constructor.

    Args:
      parser: The original command's parser.
      pubsub_arg_group: Arguments for per-subscription Pub/Sub scaling.
      release_track: The release track of the command.
    """
    self._parse_known_args = parser.parse_known_args
    self._prog = parser.prog
    self._calliope_command = parser._calliope_command
    self._pubsub_arg_group = pubsub_arg_group
    self._release_track = release_track

  def _GetPubSubFlags(self) -> frozenset[str]:
    """Returns the configured set of per-subscription Pub/Sub scaling flags."""
    args = [self._pubsub_arg_group]
    flag_names = []
    while args:
      arg = args.pop()
      if isinstance(arg, calliope_base.ArgumentGroup):
        args.extend(arg.arguments)
      else:
        flag_names.append(arg.name)
    return frozenset(flag_names)

  def _NewPubSubParser(self) -> parser_extensions.ArgumentParser:
    """Creates a new parser for parsing per-subscription Pub/Sub args."""
    parser = parser_extensions.ArgumentParser(
        add_help=False,
        prog=self._prog,
        calliope_command=self._calliope_command,
    )

    ai = parser_arguments.ArgumentInterceptor(
        parser=parser,
        is_global=False,
        cli_generator=None,
        allow_positional=True,
    )

    self._pubsub_arg_group.AddToParser(ai)
    cli.FLAG_INTERNAL_FLAG_FILE_LINE.AddToParser(ai)
    return parser

  def _CheckForPubsubFlags(self, namespace: parser_extensions.Namespace):
    """Checks that no orphan Pub/Sub flags were specified in remaining args."""
    pubsub_flags = self._GetPubSubFlags().intersection(
        namespace.GetSpecifiedArgNames()
    )
    if pubsub_flags:
      raise parser_errors.ArgumentError(
          'When {flags} is specified, --scaling-pubsub-subscription must also'
          ' be specified.',
          flags=', '.join(pubsub_flags),
      )

  def _IsFlagArg(self, arg: Any):
    return isinstance(arg, str) and arg.startswith('--')

  def _ExtractFlag(self, arg: str):
    flag = re.match(self._FLAG_PATTERN, arg)
    if flag:
      return flag.group(1)
    return None

  def _IsNonPubSubFlag(
      self, value: Any, pubsub_groups: dict[str, list[Any]]
  ) -> bool:
    return (
        bool(pubsub_groups)
        and self._IsFlagArg(value)
        and self._ExtractFlag(value) not in self._GetPubSubFlags()
    )

  def ParseKnownArgs(
      self,
      args: Sequence[Any],
      namespace: parser_extensions.Namespace,
  ) -> tuple[parser_extensions.Namespace, Sequence[Any]]:
    """Performs custom Pub/Sub scaling arg parsing.

    Groups arguments after each --scaling-pubsub-subscription flag into that
    subscription's namespace list.

    Args:
      args: The arguments to parse.
      namespace: The namespace to store parsed args in.

    Returns:
      A tuple containing the updated namespace and a list of unknown args.
    """
    remaining = []
    pubsub_groups = collections.defaultdict(list)
    current = remaining
    i = 0

    while i < len(args):
      value = args[i]
      i += 1
      if value == self._SUBSCRIPTION_FLAG_NAME:
        if i >= len(args):
          remaining.append(value)
        else:
          sub_val = args[i]
          current = pubsub_groups[sub_val]
          current.append(value)
          current.append(sub_val)
          i += 1
      elif isinstance(value, str) and value.startswith(
          self._SUBSCRIPTION_FLAG_NAME + '='
      ):
        current_sub = value.split(sep='=', maxsplit=1)[1]
        current = pubsub_groups[current_sub]
        current.append(value)
      elif value == '--':
        remaining.append(value)
        remaining.extend(args[i:])
        break
      elif self._IsNonPubSubFlag(value, pubsub_groups):
        # Non-pubsub flag after a pubsub flag: route to remaining
        remaining.append(value)
        current = remaining
      else:
        current.append(value)

    if not pubsub_groups:
      return self._parse_known_args(args=remaining, namespace=namespace)

    namespace.pubsub_scalings = []
    for _, pubsub_args in pubsub_groups.items():
      pubsub_namespace = parser_extensions.Namespace()
      pubsub_namespace = self._NewPubSubParser().parse_args(
          args=pubsub_args, namespace=pubsub_namespace
      )
      namespace.pubsub_scalings.append(pubsub_namespace)

    namespace, unknown_args = self._parse_known_args(
        args=remaining, namespace=namespace
    )
    self._CheckForPubsubFlags(namespace)
    return namespace, unknown_args
