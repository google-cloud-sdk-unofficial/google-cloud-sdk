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
"""Fetch Hub-registered cluster credentials for Connect Gateway."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.container import util as container_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import api_util as hubapi_util
from googlecloudsdk.command_lib.container.fleet import connect_gateway_util as cg_util
from googlecloudsdk.command_lib.container.fleet import gwkubeconfig_util as kconfig
from googlecloudsdk.command_lib.container.fleet.memberships import errors as memberships_errors
from googlecloudsdk.command_lib.container.fleet.memberships import util
from googlecloudsdk.command_lib.projects import util as project_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

KUBECONTEXT_FORMAT = 'connectgateway_{project}_{location}_{membership}'
SERVER_FORMAT = 'https://{service_name}/{version}/projects/{project_number}/locations/{location}/{resource_type}/{membership}'
REQUIRED_PERMISSIONS = [
    'gkehub.memberships.get',
    'gkehub.gateway.get',
    'serviceusage.services.get',
]


class GetCredentials(base.Command):
  """Fetch credentials for a fleet-registered cluster to be used in Connect Gateway.

  {command} updates the `kubeconfig` file with the appropriate credentials and
  endpoint information to send `kubectl` commands to a fleet-registered and
  connected cluster through Connect Gateway Service.

  It takes a project, passed through by set defaults or flags. By default,
  credentials are written to `$HOME/.kube/config`. You can provide an alternate
  path by setting the `KUBECONFIG` environment variable. If `KUBECONFIG`
  contains multiple paths, the first one is used.

  Upon success, this command will switch current context to the target cluster,
  when working with multiple clusters.

  ## EXAMPLES

    Get gateway kubeconfig for a registered cluster:

      $ {command} my-cluster
  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'MEMBERSHIP',
        type=str,
        help=textwrap.dedent("""\
          The membership name used to locate a cluster in your project. """),
    )
    if cls.ReleaseTrack() is base.ReleaseTrack.ALPHA:
      parser.add_argument(
          '--location',
          type=str,
          hidden=True,
          help=textwrap.dedent("""\
              The location for the membership resource, e.g. `us-central1`.
              If not specified, defaults to `global`.
            """),
      )

  def Run(self, args):
    container_util.CheckKubectlInstalled()
    project_id = properties.VALUES.core.project.GetOrFail()
    location = getattr(args, 'location', 'global')
    if location is None:
      location = 'global'

    log.status.Print('Starting to build Gateway kubeconfig...')
    log.status.Print('Current project_id: ' + project_id)

    self.RunIamCheck(project_id)
    hub_endpoint_override = properties.VALUES.api_endpoint_overrides.AllValues(
    ).get('gkehub', '')
    # API enablement is only done once per environment, regardless of which
    # region is being accessed.
    cg_util.CheckGatewayApiEnablement(
        project_id,
        util.GetConnectGatewayServiceName(hub_endpoint_override, None))

    membership = self.ReadClusterMembership(project_id, location,
                                            args.MEMBERSHIP)

    resource_type = 'memberships'
    # Change the URL for registered GKE clusters
    if self.ReleaseTrack() is base.ReleaseTrack.ALPHA or self.ReleaseTrack(
    ) is base.ReleaseTrack.BETA:
      # Probers use GKE clusters to emulate attached clusters, and so must be
      # exempt.
      if project_id == 'gkeconnect-prober':
        pass
      if (hasattr(membership, 'endpoint') and
          hasattr(membership.endpoint, 'gkeCluster') and
          membership.endpoint.gkeCluster):
        resource_type = 'gkeMemberships'

    self.GenerateKubeconfig(
        util.GetConnectGatewayServiceName(hub_endpoint_override, location),
        project_id, location, resource_type, args.MEMBERSHIP)
    msg = 'A new kubeconfig entry \"' + KUBECONTEXT_FORMAT.format(
        project=project_id, location=location, membership=args.MEMBERSHIP
    ) + '\" has been generated and set as the current context.'
    log.status.Print(msg)

  # Run IAM check, make sure caller has permission to use Gateway API.
  def RunIamCheck(self, project_id):
    project_ref = project_util.ParseProject(project_id)
    result = projects_api.TestIamPermissions(project_ref, REQUIRED_PERMISSIONS)
    granted_permissions = result.permissions

    if set(REQUIRED_PERMISSIONS) != set(granted_permissions):
      raise memberships_errors.InsufficientPermissionsError()

  def ReadClusterMembership(self, project_id, location, membership):
    resource_name = hubapi_util.MembershipRef(project_id, location, membership)
    # If membership doesn't exist, exception will be raised to caller.
    return hubapi_util.GetMembership(resource_name)

  def GenerateKubeconfig(self, service_name, project_id, location,
                         resource_type, membership):
    project_number = project_util.GetProjectNumber(project_id)
    kwargs = {
        'membership':
            membership,
        'location':
            location,
        'project_id':
            project_id,
        'server':
            SERVER_FORMAT.format(
                service_name=service_name,
                version=self.GetVersion(),
                project_number=project_number,
                location=location,
                resource_type=resource_type,
                membership=membership),
        'auth_provider':
            'gcp',
    }
    user_kwargs = {
        'auth_provider': 'gcp',
    }

    cluster_kwargs = {}
    context = KUBECONTEXT_FORMAT.format(
        project=project_id, location=location, membership=membership)
    kubeconfig = kconfig.Kubeconfig.Default()
    # Use same key for context, cluster, and user.
    kubeconfig.contexts[context] = kconfig.Context(context, context, context)
    kubeconfig.users[context] = kconfig.User(context, **user_kwargs)
    kubeconfig.clusters[context] = kconfig.Cluster(context, kwargs['server'],
                                                   **cluster_kwargs)
    kubeconfig.SetCurrentContext(context)
    kubeconfig.SaveToFile()
    return kubeconfig

  @classmethod
  def GetVersion(cls):
    if cls.ReleaseTrack() is base.ReleaseTrack.ALPHA:
      return 'v1alpha1'
    elif cls.ReleaseTrack() is base.ReleaseTrack.BETA:
      return 'v1beta1'
    elif cls.ReleaseTrack() is base.ReleaseTrack.GA:
      return 'v1'
    else:
      return ''
