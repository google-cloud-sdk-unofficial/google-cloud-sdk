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
"""Gets the protected resources summary."""


from googlecloudsdk.api_lib.kmsinventory import inventory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import resource_args

DETAILED_HELP = {
    'DESCRIPTION': """
         *{command}* returns a summary of the resources a key is protecting.

         The summary includes how many projects contain protected resources,
         how many protected resources there are, what are the types of protected
         resources, and the count for each type of protected resource.
       """,
    'EXAMPLES': """
         To view the summary of protected resources for the key `puppy`, run:

           $ {command} --keyname=puppy
       """,
}

DETAILED_HELP_ALPHA = {
    'DESCRIPTION': """
         *{command}* returns a summary of the resources a key is protecting.

         The summary includes how many projects contain protected resources,
         how many protected resources there are, what are the types of protected
         resources, and the count for each type of protected resource.
       """,
    'EXAMPLES': """
         To view the summary of protected resources for the key
         `projects/test-prj/locations/us/keyRings/us-keyring/cryptoKeys/us-key`,
         run:

           $ {command} --keyname=projects/test-prj/locations/us/keyRings/us-keyring/cryptoKeys/us-key
       """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.DefaultUniverseOnly
class GetProtectedResourcesSummary(base.Command):
  """Gets the protected resources summary."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddKmsKeyResourceArgForKMS(parser, True, '--keyname')

  def Run(self, args):
    keyname = args.keyname
    return inventory.GetProtectedResourcesSummary(keyname)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class GetProtectedResourcesSummaryWithFallback(base.Command):
  """Gets the protected resources summary."""

  detailed_help = DETAILED_HELP_ALPHA

  @staticmethod
  def Args(parser):
    resource_args.AddKmsKeyResourceArgForKMS(parser, True, '--keyname')
    parser.add_argument(
        '--fallback-scope',
        choices=['FALLBACK_SCOPE_UNSPECIFIED', 'FALLBACK_SCOPE_PROJECT'],
        help=(
            'If permission is denied at the organization level, fall back to'
            ' the project level scope.'
        ),
    )

  def Run(self, args):
    keyname = args.keyname
    fallback_scope = args.fallback_scope
    return inventory.GetProtectedResourcesSummary(keyname, fallback_scope)
