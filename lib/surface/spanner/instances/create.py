# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command for spanner instances create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import instance_operations
from googlecloudsdk.api_lib.spanner import instances
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.command_lib.spanner import resource_args


class Create(base.CreateCommand):
  """Create a Cloud Spanner instance."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To create a Cloud Spanner instance, run:

          $ {command} my-instance-id --config=regional-us-east1 --description=my-instance-display-name --nodes=3
        """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Please add arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.
    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.Instance().AddToParser(parser)
    flags.Config().AddToParser(parser)
    flags.Description().AddToParser(parser)
    resource_args.AddExpireBehaviorArg(parser)
    resource_args.AddInstanceTypeArg(parser)
    group_parser = parser.add_argument_group(mutex=True, required=False)
    flags.Nodes().AddToParser(group_parser)
    flags.ProcessingUnits().AddToParser(group_parser)
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddCacheUpdater(flags.InstanceCompleter)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    instance_type = resource_args.GetInstanceType(args)
    expire_behavior = resource_args.GetExpireBehavior(args)

    op = instances.Create(args.instance, args.config, args.description,
                          args.nodes, args.processing_units, instance_type,
                          expire_behavior)
    if args.async_:
      return op
    instance_operations.Await(op, 'Creating instance')
