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

"""Calliope JSON argument hydration library."""

from collections.abc import Mapping
import dataclasses
import json
from typing import Any

from googlecloudsdk.calliope import parser_extensions


@dataclasses.dataclass(frozen=True)
class Arg:
  """A parsed flag or positional argument from Go's clap parser."""

  name: str
  value: Any = None
  is_set: bool = False
  _dest: str | None = None

  @classmethod
  def FromDict(cls, data: Mapping[str, Any]) -> 'Arg':
    return cls(
        name=data['name'],
        value=data.get('value'),
        is_set=bool(data.get('is_set', False)),
        _dest=data.get('dest'),
    )

  @property
  def dest(self) -> str:
    return self._dest or self.name.lstrip('-').replace('-', '_')

  @property
  def cli_flag_name(self) -> str:
    return self.name if self.name.startswith('-') else f'--{self.name}'


@dataclasses.dataclass(frozen=True)
class Payload:
  """The deserialized GOCLOUD_PAYLOAD emitted by the Go CLI."""

  command_path: list[str] = dataclasses.field(default_factory=list)
  flags: tuple[Arg, ...] = ()
  args: tuple[Arg, ...] = ()

  @classmethod
  def FromJson(cls, payload_json: str) -> 'Payload':
    """Deserializes a GOCLOUD_PAYLOAD JSON string into a Payload.

    Args:
      payload_json: The raw JSON string emitted by the Go CLI.

    Returns:
      The deserialized Payload instance.

    Raises:
      ValueError: If payload_json is not valid JSON or does not match the
        expected payload schema.
    """
    try:
      data = json.loads(payload_json)
      if not isinstance(data, Mapping):
        raise ValueError(
            f'Expected a JSON object, got {type(data).__name__}'
        )
      return cls(
          command_path=list(data.get('command_path') or []),
          flags=tuple(
              Arg.FromDict(item) for item in (data.get('flags') or [])
          ),
          args=tuple(
              Arg.FromDict(item) for item in (data.get('args') or [])
          ),
      )
    except (KeyError, TypeError, ValueError) as e:
      raise ValueError(f'Invalid GOCLOUD_PAYLOAD: {e}') from e


def HydrateNamespace(calliope_command, payload: Payload):
  """Constructs and populates a Calliope Namespace from a Go payload.

  Args:
    calliope_command: calliope.backend.Command, The resolved Calliope command.
    payload: Payload, The parsed Go payload.

  Returns:
    parser_extensions.Namespace, The populated Calliope namespace object.
  """
  # NOTE: To avoid loading parent commands or configuring/parsing ancestor args
  # in Python, gocloud (Go) should:
  # 1. Supply the target argparse `dest` attribute on each flag/arg item.
  # 2. Pass property overrides via standard `CLOUDSDK_<SECTION>_<PROPERTY>`
  #    environment variables (which `properties.VALUES` reads natively).
  parser = calliope_command._parser  # pylint: disable=protected-access
  parser._calliope_command = calliope_command  # pylint: disable=protected-access
  ns = parser_extensions.Namespace()
  ns._SetParser(parser)  # pylint: disable=protected-access

  for flag in payload.flags:
    setattr(ns, flag.dest, flag.value)
    if flag.is_set:
      ns._specified_args[flag.dest] = flag.cli_flag_name  # pylint: disable=protected-access

  for arg in payload.args:
    setattr(ns, arg.dest, arg.value)
    if arg.is_set:
      ns._specified_args[arg.dest] = arg.name  # pylint: disable=protected-access

  return ns
