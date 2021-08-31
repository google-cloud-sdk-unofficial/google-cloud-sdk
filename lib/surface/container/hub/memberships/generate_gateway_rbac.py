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

import sys
import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.hub import rbac_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GenerateGatewayRbac(base.Command):
  # pylint: disable=line-too-long
  r"""Generate RBAC policy files for connected clusters.

  {command} generates RBAC policies to be used by Connect Gateway API.

  Upon success, this command will write the output RBAC policy to the designated
  local file in dry run mode.

  ## EXAMPLES
    The current implementation supports multiple modes:

    Dry run mode to generate the RBAC policy file, and write to local directory:

      $ {command} --membership=my-cluster --users=foo@example.com,test-acct@test-project.iam.gserviceaccount.com --role=clusterrole/cluster-reader --rbac-output-file=./rbac.yaml

    Dry run mode to generate the RBAC policy, and print on screen:

      $ {command} --membership=my-cluster --users=foo@example.com,test-acct@test-project.iam.gserviceaccount.com --role=clusterrole/cluster-reader

    Anthos support mode, generate the RBAC policy file with read-only permission for TSE/Eng to debug customers' clusters:

      $ {command} --membership=my-cluster --users=foo@example.com,test-acct@test-project.iam.gserviceaccount.com --anthos-support
  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--membership',
        type=str,
        help=textwrap.dedent("""\
          Membership name to assign RBAC policy with.
        """),
    )
    parser.add_argument(
        '--users',
        type=str,
        help=textwrap.dedent("""\
          User's email address or service account email address.
        """),
        required=True)
    parser.add_argument(
        '--role',
        type=str,
        help=textwrap.dedent("""\
          Namespace scoped role or cluster role.
        """),
    )
    parser.add_argument(
        '--rbac-output-file',
        type=str,
        help=textwrap.dedent("""\
          If specified, this command will execute in dry run mode and write to
          the file specified with this flag: the generated RBAC policy will not
          be applied to Kubernetes clusters,instead it will be written to the
          designated local file.
        """))
    parser.add_argument(
        '--anthos-support',
        action='store_true',
        help=textwrap.dedent("""\
          If specified, this command will generate RBAC policy
          file for anthos support.
        """),
    )

  def Run(self, args):
    log.status.Print('Validating input arguments.')
    if len(args.users) < 1:
      raise rbac_util.InvalidArgsError(
          'The required field [users] was not provided. Please specify the '
          'users or service account in this field.'
      )
    project_id = properties.VALUES.core.project.GetOrFail()

    # Validate the args value before generate the RBAC policy file.
    rbac_util.ValidateArgs(args)

    # Generate the RBAC policy file from args.
    generated_rbac = rbac_util.GenerateRBAC(args, project_id)

    sys.stdout.write('--------------------------------------------')
    sys.stdout.write('Generated RBAC policy file is: ')

    # Write the generated RBAC policy file to the file provided with
    # "--rbac-output-file" specified or print on the screen.
    log.WriteToFileOrStdout(
        args.rbac_output_file if args.rbac_output_file else '-',
        generated_rbac,
        overwrite=True,
        binary=False,
        private=True)
