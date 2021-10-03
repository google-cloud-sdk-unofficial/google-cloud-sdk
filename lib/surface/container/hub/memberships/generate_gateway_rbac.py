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
from googlecloudsdk.command_lib.container.hub import kube_util
from googlecloudsdk.command_lib.container.hub import rbac_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files as file_utils


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

    Anthos support mode, generate the RBAC policy file with read-only permission
    for TSE/Eng to debug customers' clusters:

      $ {command} --membership=my-cluster --anthos-support

    Apply mode, generate the RBAC policy and apply it to the specified cluster:

      $ {command} --membership=my-cluster --users=foo@example.com,test-acct@test-project.iam.gserviceaccount.com --role=clusterrole/cluster-reader --context=my-cluster-contex --kubeconfig=/home/user/custom_kubeconfig --apply
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
    )
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
    parser.add_argument(
        '--apply',
        action='store_true',
        help=textwrap.dedent("""\
          If specified, this command will generate RBAC policy and apply to the
          specified cluster.
        """),
    )
    parser.add_argument(
        '--context',
        type=str,
        help=textwrap.dedent("""\
          The cluster context as it appears in the kubeconfig file. You can get
        this value from the command line by running command:
        `kubectl config current-context`.
        """),
    )
    parser.add_argument(
        '--kubeconfig',
        type=str,
        help=textwrap.dedent("""\
            The kubeconfig file containing an entry for the cluster. Defaults to
            $KUBECONFIG if it is set in the environment, otherwise defaults to
            $HOME/.kube/config.
          """),
    )

  def Run(self, args):
    log.status.Print('Validating input arguments.')
    project_id = properties.VALUES.core.project.GetOrFail()

    # Validate the args value before generate the RBAC policy file.
    rbac_util.ValidateArgs(args)

    # Generate the RBAC policy file from args.
    generated_rbac = rbac_util.GenerateRBAC(args, project_id)

    if args.rbac_output_file:
      sys.stdout.write('Generated RBAC policy is written to file: {} \n'.format(
          args.rbac_output_file))
    else:
      sys.stdout.write('Generated RBAC policy is: \n')
      sys.stdout.write('--------------------------------------------\n')

    # Write the generated RBAC policy file to the file provided with
    # "--rbac-output-file" specified or print on the screen.
    log.WriteToFileOrStdout(
        args.rbac_output_file if args.rbac_output_file else '-',
        generated_rbac,
        overwrite=True,
        binary=False,
        private=True)

    # Apply generated RBAC policy to cluster.
    if args.apply:
      sys.stdout.write(
          'Applying the generate RBAC policy to cluster with kubeconfig: {}, context: {}\n'
          .format(args.kubeconfig, args.context))

      with file_utils.TemporaryDirectory() as tmp_dir:
        file = tmp_dir + '/rbac.yaml'
        file_utils.WriteFileContents(file, generated_rbac)
        with kube_util.KubernetesClient(
            kubeconfig=getattr(args, 'kubeconfig', None),
            context=getattr(args, 'context', None),
        ) as kube_client:
          # Check Admin permissions.
          kube_client.CheckClusterAdminPermissions()
          # Get previous RBAC policy from cluster.
          prev_rbac_name, rbac_policy_type, prev_rbac_policy = kube_client.GetRbacPolicy(
              args.membership, args.role, project_id,
              True if args.anthos_support else False)
          # Check to override the existing RBAC policy or not.
          if prev_rbac_policy:
            message = ('A RBAC policy: {}/{} already exist. Do you want to override the current RBAC policy file?\n'.format(
                rbac_policy_type, prev_rbac_name))
            console_io.PromptContinue(
                message=message,
                cancel_on_no=True)

          try:
            kube_client.ApplyRbacPolicy(file)
          except Exception as e:
            log.status.Print(
                'Error in applying the RBAC policy to cluster: {}\n'.format(e))
            raise
          log.status.Print('Successfully applied the RBAC policy to cluster.\n')
