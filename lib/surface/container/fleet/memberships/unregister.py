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
"""The unregister-cluster command for removing clusters from the fleet."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import agent_util
from googlecloudsdk.command_lib.container.fleet import api_util
from googlecloudsdk.command_lib.container.fleet import exclusivity_util
from googlecloudsdk.command_lib.container.fleet import kube_util
from googlecloudsdk.command_lib.container.fleet import util as hub_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Unregister(base.DeleteCommand):
  r"""Unregister a cluster from Fleet.

  This command unregisters a cluster with the fleet by:

    1. Deleting the Fleet Membership resource for this cluster (a.k.a
       `{parent_command} delete`).
    2. Removing the corresponding in-cluster Kubernetes Resources that make the
       cluster exclusive to one fleet (a.k.a `kubectl delete memberships
       membership`).
    3. Uninstalling the Connect Agent from this cluster (a.k.a
       `kubectl delete on the gke-connect namespace`).

  The unregister command makes additional internal checks to ensure that all
  three steps can be safely done to properly clean-up in-Fleet and in-cluster
  resources.

  To register a non-GKE cluster use --context flag (with an optional
  --kubeconfig flag).

  To register a GKE cluster use --gke-cluster or --gke-uri flag (no --kubeconfig
  flag is required).

  To only delete the Fleet membership resource, consider using the command:
  `{parent_command} delete`. This command is intended to delete stale Fleet
  Membership resources as doing so on a fully registered cluster will skip some
  of the steps above and orphan in-cluster resources and agent connections to
  Google.

  ## EXAMPLES

    Unregister a non-GKE cluster referenced from a specific kubeconfig file:

      $ {command} my-membership \
        --context=my-cluster-context \
        --kubeconfig=/home/user/custom_kubeconfig

    Unregister a non-GKE cluster referenced from the default kubeconfig file:

      $ {command} my-membership --context=my-cluster-context

    Unregister a GKE cluster referenced from a GKE URI:

      $ {command} my-membership \
        --gke-uri=my-cluster-gke-uri

    Unregister a GKE cluster referenced from a GKE Cluster location and name:

      $ {command} my-membership \
        --gke-cluster=my-cluster-region-or-zone/my-cluster

  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'MEMBERSHIP_NAME',
        type=str,
        help=textwrap.dedent("""\
            The membership name that corresponds to the cluster being
            unregistered. To get list of all the memberships on the Fleet,
            consider using the command: `{parent_command} list`.
         """),
    )
    if cls.ReleaseTrack() is base.ReleaseTrack.ALPHA:
      parser.add_argument(
          '--location',
          type=str,
          hidden=True,
          help=textwrap.dedent("""\
              The location for the membership resource, e.g. `us-central1`.
              If not specified, defaults to `global`. Not supported for GKE clusters.
            """),
      )
    hub_util.AddClusterConnectionCommonArgs(parser)

  def Run(self, args):
    project = arg_utils.GetFromNamespace(args, '--project', use_defaults=True)

    kube_client = kube_util.KubernetesClient(
        gke_uri=getattr(args, 'gke_uri', None),
        gke_cluster=getattr(args, 'gke_cluster', None),
        kubeconfig=getattr(args, 'kubeconfig', None),
        context=getattr(args, 'context', None),
        public_issuer_url=getattr(args, 'public_issuer_url', None),
        enable_workload_identity=getattr(args, 'enable_workload_identity',
                                         False),
    )
    location = getattr(args, 'location', 'global')
    if location is None:
      location = 'global'
    kube_client.CheckClusterAdminPermissions()
    kube_util.ValidateClusterIdentifierFlags(kube_client, args)
    membership_id = args.MEMBERSHIP_NAME

    # Delete membership from Fleet API.
    try:
      name = 'projects/{}/locations/{}/memberships/{}'.format(
          project, location, membership_id)
      obj = api_util.GetMembership(name, self.ReleaseTrack())
      if not obj.externalId:
        console_io.PromptContinue(
            'invalid membership {0} does not have '
            'external_id field set. We cannot determine '
            'if registration is requested against a '
            'valid existing Membership. Consult the '
            'documentation on container fleet memberships '
            'update for more information or run gcloud '
            'container fleet memberships delete {0} if you '
            'are sure that this is an invalid or '
            'otherwise stale Membership'.format(membership_id),
            cancel_on_no=True)
      uuid = kube_util.GetClusterUUID(kube_client)
      if obj.externalId != uuid:
        raise exceptions.Error(
            'Membership [{}] is not associated with the cluster you are trying'
            ' to unregister. Please double check the cluster identifier that you'
            ' have supplied.'.format(membership_id))

      api_util.DeleteMembership(name, self.ReleaseTrack())
    except apitools_exceptions.HttpUnauthorizedError as e:
      raise exceptions.Error(
          'You are not authorized to unregister clusters from project [{}]. '
          'Underlying error: {}'.format(project, e))
    except apitools_exceptions.HttpNotFoundError as e:
      log.status.Print(
          'Membership [{}] for the cluster [{}] was not found on the Fleet. '
          'It may already have been deleted, or it may never have existed.'
          .format(name, args.MEMBERSHIP_NAME))

    # Get namespace for the connect resource label.
    selector = '{}={}'.format(agent_util.CONNECT_RESOURCE_LABEL, project)
    namespaces = kube_client.NamespacesWithLabelSelector(selector)
    if not namespaces:
      log.status.Print('There\'s no namespace for the label [{}]. '
                       'If [gke-connect] is labeled with another project, '
                       'You\'ll have to manually delete the namespace. '
                       'You can find all namespaces by running:\n'
                       '  `kubectl get ns -l {}`'.format(
                           agent_util.CONNECT_RESOURCE_LABEL,
                           agent_util.CONNECT_RESOURCE_LABEL))

    # Delete in-cluster membership resources.
    try:
      parent = api_util.ParentRef(project, location)
      cr_manifest = kube_client.GetMembershipCR()

      res = api_util.ValidateExclusivity(cr_manifest, parent, membership_id,
                                         self.ReleaseTrack())
      if res.status.code:
        console_io.PromptContinue(
            'Error validating cluster\'s exclusivity state with the Fleet under '
            'parent collection [{}]: {}. The cluster you are trying to unregister'
            ' is not associated with the membership [{}]. Continuing will delete'
            ' membership related resources from your cluster, and the cluster'
            ' will lose its association to the Fleet in project [{}] and can be'
            ' registered into a different project. '.format(
                parent, res.status.message, membership_id, project),
            cancel_on_no=True)
      exclusivity_util.DeleteMembershipResources(kube_client)
    except exceptions.Error as e:
      log.status.Print(
          '{} error in deleting in-cluster membership resources. '
          'You can manually delete these membership related '
          'resources from your cluster by running the command:\n'
          '  `kubectl delete memberships membership`.\nBy doing so, '
          'the cluster will lose its association to the Fleet in '
          'project [{}] and can be registered into a different '
          'project. '.format(e, project))

    # Delete the connect agent.
    agent_util.DeleteConnectNamespace(kube_client, args)
