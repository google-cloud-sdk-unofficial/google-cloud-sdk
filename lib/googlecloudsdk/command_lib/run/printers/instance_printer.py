# third_party/py/googlecloudsdk/command_lib/run/printers/instance_printer.py
# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Instance-specific printer."""


import textwrap

from googlecloudsdk.api_lib.run import instance
from googlecloudsdk.command_lib.run.printers import container_and_volume_printer_util as container_util
from googlecloudsdk.command_lib.run.printers import k8s_object_printer_util as k8s_util
from googlecloudsdk.command_lib.run.printers import traffic_printer
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import custom_printer_base as cp
from googlecloudsdk.core.util import times


def StatusColorFormat():
  """Return the color format string for the status of this instance."""
  color_formatters = []
  for _, symbol in instance.Instance.INSTANCE_SYMBOLS.items():
    if symbol.color:
      color_formatters.append(f'{symbol.color}="[{symbol.best}{symbol.alt}]"')
  color_formatters_str = ','.join(color_formatters)
  return f'ready_symbol.color({color_formatters_str}):label=""'


INSTANCE_PRINTER_FORMAT = 'instance'


def _GetRestartPolicy(record):
  """Gets the restart policy of this instance."""
  if (
      record.spec
      and hasattr(record.spec, 'restartPolicy')
      and record.spec.restartPolicy
  ):
    return record.spec.restartPolicy
  return 'OnFailure'


def _GetRunningForMessage(record):
  """Returns formatted message containing running duration for instance."""
  original_msg = ''
  if record.ready_condition and record.ready_condition.get('message'):
    original_msg = record.ready_condition['message']

  if record.is_running and record.last_transition_time:
    try:
      start_time = times.ParseDateTime(record.last_transition_time)
      now = times.Now(times.UTC)
      delta = now - start_time
      if delta.total_seconds() >= 0:
        duration_str = k8s_util.FormatDurationShort(int(delta.total_seconds()))
        if original_msg:
          return f'Instance uptime: {duration_str}. {original_msg}'
        return f'Instance uptime: {duration_str}.'
    except (TypeError, ValueError, AttributeError, times.Error):
      pass
  return original_msg


class InstancePrinter(cp.CustomPrinterBase):
  """Prints the run Instance in a custom human-readable format.

  Format specific to Cloud Run instances. Only available on Cloud Run commands
  that print instances.
  """

  @staticmethod
  def FormatReadyMessage(record):
    ready_message = _GetRunningForMessage(record)
    if ready_message:
      _, color = record.ReadySymbolAndColor()
      return console_attr.GetConsoleAttr().Colorize(
          textwrap.fill(ready_message, 100),
          color,
      )
    return ''

  @staticmethod
  def GetConfig(record):
    config = []
    return cp.Lines(config)

  @staticmethod
  def _formatOutput(record):
    output = []
    header = k8s_util.BuildHeader(record)
    ready_message = InstancePrinter.FormatReadyMessage(record)
    labels = k8s_util.GetLabels(record.labels)
    config = InstancePrinter.GetConfig(record)
    route_fields_section = traffic_printer.TransformInstanceRouteFields(record)
    # pylint: disable=protected-access
    route_fields_list = (
        list(route_fields_section._lines) if route_fields_section else []
    )
    restart_policy = _GetRestartPolicy(record)
    if restart_policy:
      route_fields_list.append(
          cp.Labeled([('Restart Policy', restart_policy)])
      )
    route_fields = (
        cp.Section(route_fields_list, max_column_width=60)
        if route_fields_list
        else None
    )
    containers = container_util.GetContainers(record)

    if header:
      output.append(header)
    if ready_message:
      output.append(ready_message)
    if labels:
      output.append(labels)
    output.append(' ')

    if route_fields:
      output.append(route_fields)
      output.append(' ')

    output.append(containers)
    output.append(config)

    return output

  def Transform(self, record):
    """Transform a instance into the output structure of marker classes."""
    return cp.Lines(InstancePrinter._formatOutput(record))
