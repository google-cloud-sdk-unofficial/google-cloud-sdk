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
"""`gcloud access-context-manager perimeters dry-run reset` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import zones as zones_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.accesscontextmanager import perimeters
from googlecloudsdk.command_lib.accesscontextmanager import policies


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ResetPerimeterDryRunAlpha(base.DeleteCommand):
  """Resets the dry-run state of a Service Perimeter.

  Resets the dry-run state such that the new dry-run state is the same as the
  enforced configuration. No audit logs will be generated in this state.

  The `use_explicit_dry_run_spec` field of the Service Perimeter is set to
  false after this operation, and the `spec` field, which contains the dry-run
  configuration, is deleted.

  ## EXAMPLES

  To reset the dry-run configuration for a Service Perimeter:

      $ {command} my-perimeter
  """
  _API_VERSION = 'v1alpha'

  @staticmethod
  def Args(parser):
    perimeters.AddResourceArg(parser, 'to reset')
    parser.add_argument(
        '--async',
        action='store_true',
        help="""Return immediately, without waiting for the operation in
            progress to complete.""")

  def Run(self, args):
    client = zones_api.Client(version=self._API_VERSION)
    perimeter_ref = args.CONCEPTS.perimeter.Parse()
    policies.ValidateAccessPolicyArg(perimeter_ref, args)
    return client.UnsetSpec(perimeter_ref, use_explicit_dry_run_spec=False)
