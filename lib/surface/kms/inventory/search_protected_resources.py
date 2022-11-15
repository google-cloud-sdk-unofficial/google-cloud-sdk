# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Searches the protected resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kmsinventory import inventory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import resource_args
from googlecloudsdk.command_lib.resource_manager import completers

DETAILED_HELP = {
    'DESCRIPTION': """
         TODO
       """,
    'EXAMPLES': """
         TODO
       """,
}


class SearchProtectedResources(base.ListCommand):
  """Searches the resources protected by a key."""
  # TODO(b/255752383) finish writing help text
  # detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddKmsKeyResourceArgForKMS(parser, True, '--keyname')
    parser.add_argument(
        '--scope',
        metavar='ORGANIZATION_ID',
        completer=completers.OrganizationCompleter,
        required=True,
        help='Organization ID.')

  def Run(self, args):
    key_name = args.keyname
    org = args.scope
    return inventory.SearchProtectedResources(
        scope=org, key_name=key_name, args=args)
