# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Implementation of gcloud Procurement consumer order allocation create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.commerce_procurement import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.commerce_procurement import flags
from googlecloudsdk.command_lib.commerce_procurement import resource_args


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Creates the Order Allocation resource from the Create API."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.ArgumentParser to register arguments with.
    """
    resource_args.AddOrderParentResourceArg(
        parser, 'Parent order to create order allocation under.')
    parser.add_argument(
        '--display-name', help='Display name of the order allocation.')

    flags.AddOrderAllocationEntryArgs(parser)

  def Run(self, args):
    """Runs the command.

    Args:
      args: The arguments that were provided to this command invocation.

    Returns:
      An Order Allocation operation.
    """
    order_ref = args.CONCEPTS.order.Parse()
    return apis.OrderAllocations.Create(
        order_ref.RelativeName(), args.display_name, args.int64_resource_value,
        args.double_resource_value, args.string_resource_value, args.targets)
