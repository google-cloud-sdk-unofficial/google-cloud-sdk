# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Generate RBAC policy files for Connect Gateway users."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class InstallGatewayRbac(base.Command):
  # pylint: disable=line-too-long
  r"""Generate RBAC policy files for connected clusters.

  {command} generates RBAC policies to be used by Connect Gateway API.

  Upon success, this command will write the output RBAC policy to the designated
  local file in dry run mode.

  ## EXAMPLES

    Dry run mode to generate the RBAC policy file, and write to local directory:

      $ {command} my-cluster --users=foo@example.com,test-acct@test-project.iam.gserviceaccount.com --role=clusterrole/cluster-reader --output=./rbac.yaml
  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'MEMBERSHIP',
        type=str,
        help=textwrap.dedent('The membership name to assign RBAC policy with.'),
    )
    parser.add_argument(
        '--users',
        type=str,
        help=textwrap.dedent("""\
          The user's email address or service account email address.
        """),
        required=True)
    parser.add_argument(
        '--role',
        type=str,
        help=textwrap.dedent("""\
          The namespace scoped role or cluster role.
        """),
        required=True)
    parser.add_argument(
        '--output',
        type=str,
        help=textwrap.dedent("""\
          When have this flag enabled, this command will be in dry run mode: the
          generated RBAC policy will not be applied to Kubernetes clusters,
          instead it will be written to the designated local file.
        """))

  def Run(self, args):
    log.status.Print('Validating input arguments.')

    # Check the required field's values are not empty.
    if len(args.MEMBERSHIP) < 1:
      raise exceptions.Error(
          'The required property [membership] was not provided. Please specify the cluster name in this field.'
      )
    if len(args.users) < 1:
      raise exceptions.Error(
          'The required field [users] was not provided. Please specify the users or service account in this field.'
      )
    if len(args.role) < 1:
      raise exceptions.Error(
          'The required field [role] was not provided. Please specify the cluster role or namespace role in this field.'
      )
    if len(args.output) < 1:
      raise exceptions.Error(
          'The required field [output] was not provided. Please specify the output path in this field.'
      )
    project_id = arg_utils.GetFromNamespace(
        args, '--project', use_defaults=True)
    if len(project_id) < 1:
      raise exceptions.Error(
          'The required field [project] was not provided. It should be your project ID'
      )
    return True
