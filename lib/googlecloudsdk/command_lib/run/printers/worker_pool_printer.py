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
"""WorkerPool specific printer."""

import json

from googlecloudsdk.api_lib.run import worker_pool
from googlecloudsdk.command_lib.run.printers import instance_split_printer
from googlecloudsdk.command_lib.run.printers import k8s_object_printer_util as k8s_util
from googlecloudsdk.command_lib.run.printers import worker_pool_revision_printer
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import custom_printer_base as cp

WORKER_POOL_PRINTER_FORMAT = 'workerpool'
_PUBSUB_SCALINGS_ANNOTATION = 'run.googleapis.com/pubsubScalings'
_CPU_UTILIZATION_ANNOTATION = 'run.googleapis.com/scaling-cpu-target'


def _FormatCpuTarget(cpu_target: str | None) -> str | None:
  """Formats CPU target value as percentage string."""
  if not cpu_target or cpu_target == 'disabled':
    return None
  if cpu_target.endswith('%'):
    return cpu_target
  try:
    val = float(cpu_target)
  except (ValueError, TypeError):
    return cpu_target

  if val <= 0:
    return None
  pct = val * 100
  if pct == int(pct):
    return f'{int(pct)}%'
  return f'{pct:g}%'


class WorkerPoolPrinter(cp.CustomPrinterBase):
  """Prints the run WorkerPool in a custom human-readable format.

  Format specific to Cloud Run worker pools. Only available on Cloud Run
  commands
  that print worker pools.
  """

  with_sub_scalings = False

  def _BuildWorkerPoolHeader(self, record):
    con = console_attr.GetConsoleAttr()
    status = con.Colorize(*record.ReadySymbolAndColor())
    try:
      place = 'region ' + record.region
    except KeyError:
      place = 'namespace ' + record.namespace
    return con.Emphasize(
        '{} {} {} in {}'.format(status, 'WorkerPool', record.name, place)
    )

  def _GetRevisionHeader(self, record):
    header = ''
    if record.status is None:
      header = 'Unknown revision'
    else:
      header = 'Revision {}'.format(record.status.latestCreatedRevisionName)
    return console_attr.GetConsoleAttr().Emphasize(header)

  def _RevisionPrinters(self, record):
    """Adds printers for the revision."""
    return cp.Lines([
        self._GetRevisionHeader(record),
        k8s_util.GetLabels(record.template.labels),
        worker_pool_revision_printer.WorkerPoolRevisionPrinter.TransformSpec(
            record.template
        ),
    ])

  def _GetWorkerPoolSettings(self, record):
    """Adds worker pool level values."""
    labels = [
        cp.Labeled([
            ('Binary Authorization', k8s_util.GetBinAuthzPolicy(record)),
        ])
    ]

    scaling_setting = self._GetScalingSetting(record)
    if scaling_setting is not None:
      labels.append(scaling_setting)

    breakglass_value = k8s_util.GetBinAuthzBreakglass(record)
    if breakglass_value is not None:
      # Show breakglass even if empty, but only if set. There's no skip_none
      # option so this the workaround.
      breakglass_label = cp.Labeled([
          ('Breakglass Justification', breakglass_value),
      ])
      breakglass_label.skip_empty = False
      labels.append(breakglass_label)
    description = k8s_util.GetDescription(record)
    if description is not None:
      description_label = cp.Labeled([
          ('Description', description),
      ])
      labels.append(description_label)

    labels.append(cp.Labeled([
        ('Threat Detection', k8s_util.GetThreatDetectionEnabled(record)),
    ]))
    return cp.Section(labels)

  def _GetSubScalings(self, record):
    """Returns sub-scaling signals (Pub/Sub, CPU) for worker pool."""
    sub_scalings = []
    pubsub_str = record.annotations.get(_PUBSUB_SCALINGS_ANNOTATION, '')
    pubsub_list = None
    if pubsub_str:
      try:
        pubsub_list = json.loads(pubsub_str)
      except (ValueError, TypeError):
        pass
    if pubsub_list:
      sub_rows = []
      for item in pubsub_list:
        sub = item.get('subscription', '')
        metric = item.get('metric')
        target = item.get('targetValue')
        metric_labels = []
        if metric:
          metric_labels.append(('Metric', metric))
        if target is not None:
          metric_labels.append(('Target', str(target)))
        sub_section = cp.Section([cp.Labeled(metric_labels)])
        sub_rows.append(('Subscription: %s' % sub, sub_section))
      if sub_rows:
        pubsub_table = cp.Table(sub_rows)
        sub_scalings.append(
            cp.Labeled([('Pub/Sub', cp.Section([pubsub_table]))])
        )

    cpu_target = record.annotations.get(_CPU_UTILIZATION_ANNOTATION, '')
    formatted_cpu = _FormatCpuTarget(cpu_target)
    if formatted_cpu:
      cpu_section = cp.Section([cp.Labeled([('Target', formatted_cpu)])])
      sub_scalings.append(cp.Labeled([('CPU', cpu_section)]))

    return sub_scalings

  def _GetScalingSetting(self, record):
    """Returns the scaling setting for the worker pool."""
    scaling_mode = record.annotations.get(
        worker_pool.WORKER_POOL_SCALING_MODE_ANNOTATION, ''
    )

    if scaling_mode == 'manual':
      instance_count = record.annotations.get(
          worker_pool.MANUAL_INSTANCE_COUNT_ANNOTATION, ''
      )
      return cp.Labeled([
          ('Scaling', 'Manual (Instances: %s)' % instance_count),
      ])
    else:
      min_instance_count = record.annotations.get(
          worker_pool.WORKER_POOL_MIN_SCALE_ANNOTATION, '0'
      )
      max_instance_count = record.annotations.get(
          worker_pool.WORKER_POOL_MAX_SCALE_ANNOTATION, ''
      )
      if max_instance_count:
        scaling_header = 'Auto (Min: %s, Max: %s)' % (
            min_instance_count,
            max_instance_count,
        )
      else:
        scaling_header = 'Auto (Min: %s)' % min_instance_count

      if self.with_sub_scalings:
        sub_scalings = self._GetSubScalings(record)
        if sub_scalings:
          return cp.Table([
              ('Scaling: %s' % scaling_header, cp.Section(sub_scalings)),
          ])
      return cp.Labeled([('Scaling', scaling_header)])

  def Transform(self, record):
    """Transform a worker pool into the output structure of marker classes."""
    worker_pool_settings = self._GetWorkerPoolSettings(record)
    fmt = cp.Lines([
        self._BuildWorkerPoolHeader(record),
        k8s_util.GetLabels(record.labels),
        ' ',
        instance_split_printer.TransformInstanceSplitFields(record),
        ' ',
        worker_pool_settings,
        (' ' if worker_pool_settings.WillPrintOutput() else ''),
        cp.Labeled([(
            k8s_util.LastUpdatedMessage(record),
            self._RevisionPrinters(record),
        )]),
        k8s_util.FormatReadyMessage(record),
    ])
    return fmt


class WorkerPoolPrinterAlpha(WorkerPoolPrinter):
  """Prints the run WorkerPool in a custom human-readable format with Alpha features."""

  with_sub_scalings = True
