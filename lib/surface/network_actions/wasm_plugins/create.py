# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""gcloud network-actions wasm-plugins create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.network_actions import wasm_plugin_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_actions import flags
from googlecloudsdk.command_lib.network_actions import util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _GetLogConfig(args):
  """Converts the dict representation of the log_config to proto.

  Args:
    args: args with log_level parsed ordered dict. If log-level flag is set,
          enable option should also be set.

  Returns:
    a value of messages.WasmPluginLogConfig or None,
    if log-level flag were not provided.
  """

  if args.log_config is None:
    return None
  return util.GetLogConfig(args.log_config[0])


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a WasmPlugin."""

  detailed_help = {
      'DESCRIPTION':
          textwrap.dedent("""Create a new WasmPlugin."""),
      'EXAMPLES':
          textwrap.dedent("""\
          To create a WasmPlugin called `my-plugin`, run:

          $ {command} my-plugin
          """)
  }

  @classmethod
  def Args(cls, parser):
    flags.AdddWasmPluginResource(
        parser=parser,
        api_version=util.GetApiVersion(cls.ReleaseTrack()),
    )

    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)
    flags.AddDescriptionFlag(parser)
    flags.AddLogConfigFlag(parser)

  def Run(self, args):
    client = wasm_plugin_api.Client(self.ReleaseTrack())

    wasm_plugin_ref = args.CONCEPTS.wasm_plugin.Parse()
    labels = labels_util.ParseCreateArgs(
        args, client.messages.WasmPlugin.LabelsValue
    )
    log_config = _GetLogConfig(args)

    op_ref = client.CreateWasmPlugin(
        parent=wasm_plugin_ref.Parent().RelativeName(),
        name=wasm_plugin_ref.Name(),
        description=args.description,
        labels=labels,
        log_config=log_config,
    )

    log.status.Print('Create request issued for: [{}]'.format(
        wasm_plugin_ref.Name()))

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    wasm_plugin = client.WaitForOperation(
        operation_ref=op_ref,
        message='Waiting for operation [{}] to complete'.format(op_ref.name),
    )

    log.status.Print(
        'Created WasmPlugin [{}].'.format(wasm_plugin_ref.Name())
    )

    return wasm_plugin
