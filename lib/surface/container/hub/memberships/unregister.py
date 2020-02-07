# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""The unregister-cluster command for removing clusters from the Hub."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.hub import agent_util
from googlecloudsdk.command_lib.container.hub import api_util
from googlecloudsdk.command_lib.container.hub import exclusivity_util
from googlecloudsdk.command_lib.container.hub import kube_util
from googlecloudsdk.command_lib.container.hub import util as hub_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


class Unregister(base.DeleteCommand):
  r"""Unregister a cluster from Hub.

  This command deletes the membership resource of a registered cluster on the
  Hub and removes the connect-agent that was installed on the registered
  cluster during registration. To delete only the membership of a registered
  cluster on the Hub, consider using: `{parent_command} delete` command.


  ## EXAMPLES

    Unregister a cluster referenced from the default kubeconfig file:

      $ {command} --context=my-cluster-context

    Unregister a cluster referenced from a specific kubeconfig file:

      $ {command} \
        --context=my-cluster-context \
        --kubeconfig=/home/user/custom_kubeconfig

    Unregister a GKE cluster:

      $ {command} --context=my-gke-cluster-context
      $ {command} --gke-uri=my-gke-cluster-uri
      $ {command} --gke-cluster=my-gke-cluster-region-or-zone/my-cluster
  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'CLUSTER_NAME',
        type=str,
        help=textwrap.dedent("""\
            The name of the cluster being unregistered. This name corresponds
            to the cluster's membership resource name. To list of all the
            memberships inside your project, consider using the command:
            `{parent_command} clusters list`.
         """),
    )
    hub_util.AddUnRegisterCommonArgs(parser)

  def Run(self, args):
    project = arg_utils.GetFromNamespace(args, '--project', use_defaults=True)
    kube_client = kube_util.KubernetesClient(args)
    membership_id = args.CLUSTER_NAME
    # Delete membership from Hub API.
    try:
      name = 'projects/{}/locations/global/memberships/{}'.format(
          project, membership_id)
      api_util.DeleteMembership(name, self.ReleaseTrack())
    except apitools_exceptions.HttpUnauthorizedError as e:
      raise exceptions.Error(
          'You are not authorized to unregister clusters from project [{}]. '
          'Underlying error: {}'.format(project, e))
    except apitools_exceptions.HttpNotFoundError as e:
      log.status.Print(
          'Membership for [{}] was not found. It may already have been '
          'deleted, or it may never have existed.'.format(
              args.context))

    # Get namespace for the connect resource label.
    selector = '{}={}'.format(agent_util.CONNECT_RESOURCE_LABEL, project)
    namespaces = kube_client.NamespacesWithLabelSelector(selector)
    if not namespaces:
      log.status.Print('There\'s no namespace for the label {}. '
                       'If gke-connect is labeled with another project,'
                       'You\'ll have to manually delete the namespace.'
                       'You can find all namespaces by running:\n\n'
                       '  `kubectl get ns -l {}`'.format(
                           hub_util.CONNECT_RESOURCE_LABEL,
                           hub_util.CONNECT_RESOURCE_LABEL))

    # Delete membership resources.
    try:
      exclusivity_util.DeleteMembershipResources(kube_client)
    except exceptions.Error:
      log.status.Print('{} You can delete the membership CR manually by '
                       '`kubectl delete memberships membership`.')

    # Delete the connect agent.
    agent_util.DeleteConnectNamespace(args)
