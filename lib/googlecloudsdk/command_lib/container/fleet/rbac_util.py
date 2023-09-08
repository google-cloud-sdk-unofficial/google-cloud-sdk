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
"""Utils for GKE Connect generate gateway RBAC policy files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import re

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.command_lib.container.fleet import util as hub_util
from googlecloudsdk.command_lib.container.fleet.memberships import errors as memberships_errors
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log

CLUSTER_ROLE = 'clusterrole'
NAMESPACE_ROLE = 'role'
ANTHOS_SUPPORT_USER = 'service-{project_number}@gcp-sa-{instance_name}anthossupport.iam.gserviceaccount.com'
PRINCIPAL_USER_FORMAT = [
    'principal:',
    '',
    'iam.googleapis.com',
    'locations',
    'workforcePools',
    'subject',
]
PRINCIPAL_GROUP_FORMAT = [
    'principal:',
    '',
    'iam.googleapis.com',
    'locations',
    'workforcePools',
    'group',
]
UNWANTED_CHARS = [' ', '/', '%']
INVALID_ARGS_USER_MESSAGE = (
    'Please specify the --users in the correct format:'
    '"foo@example.com" or "principal://iam.googleapis.com/locations/global/'
    'workforcePools/pool/subject/user".'
)
INVALID_ARGS_GROUP_MESSAGE = (
    'Please specify the --groups in the correct format:'
    '"group@example.com" or "principal://iam.googleapis.com/locations/global/'
    'workforcePools/pool/group/group1".'
)
IMPERSONATE_POLICY_FORMAT = """\
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: gateway-impersonate-{metadata_name}
  labels:
    connect.gke.io/owner-feature: connect-gateway
rules:
- apiGroups:
  - ""
  resourceNames:{user_account}
  resources:
  - users
  verbs:
  - impersonate
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: gateway-impersonate-{metadata_name}
  labels:
    connect.gke.io/owner-feature: connect-gateway
roleRef:
  kind: ClusterRole
  name: gateway-impersonate-{metadata_name}
  apiGroup: rbac.authorization.k8s.io
subjects:
- kind: ServiceAccount
  name: connect-agent-sa
  namespace: gke-connect
"""
PERMISSION_POLICY_CLUSTER_FORMAT = """\
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: gateway-permission-{metadata_name}
  labels:
    connect.gke.io/owner-feature: connect-gateway
subjects:{users}
roleRef:
  kind: ClusterRole
  name: {permission}
  apiGroup: rbac.authorization.k8s.io
---
"""
PERMISSION_POLICY_NAMESPACE_FORMAT = """\
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: gateway-permission-{metadata_name}
  labels:
    connect.gke.io/owner-feature: connect-gateway
  namespace: {namespace}
subjects:{users}
roleRef:
  kind: Role
  name: {permission}
  apiGroup: rbac.authorization.k8s.io
---
"""
PERMISSION_POLICY_ANTHOS_SUPPORT_FORMAT = """\
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: anthos-support-reader
  labels:
    connect.gke.io/owner-feature: connect-gateway
rules:
- apiGroups: ["acme.cert-manager.io"]
  resources: ["challenges", "orders"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["addon.baremetal.cluster.gke.io"]
  resources: ["addonmanifests", "addonoverrides", "addons", "addonsets", "addonsettemplates"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["addons.gke.io"]
  resources: ["metricsserver", "monitoring", "stackdrivers"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["admissionregistration.k8s.io"]
  resources: ["mutatingwebhookconfigurations", "validatingwebhookconfigurations"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["anthos.gke.io"]
  resources: ["entitlements"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apiextensions.k8s.io"]
  resources: ["customresourcedefinitions"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apiregistration.k8s.io"]
  resources: ["apiservices"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apiserver.k8s.io"]
  resources: ["flowschemas", "prioritylevelconfigurations"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["controllerrevisions", "daemonsets", "deployments", "replicasets", "statefulset"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps.k8s.io"]
  resources: ["applications"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["baremetal.cluster.gke.io"]
  resources: ["addonconfigurations", "clustercidrconfigs", "clustercredentials", "clustermanifestdeployments", "clusters", "inventorymachines", "machineclasses", "machinecredentials", "machines", "nodepools"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["cronjobs", "jobs"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["bootstrap.cluster.x-k8s.io"]
  resources: ["kubeadmconfigs", "kubeadmconfigtemplates"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["bundle.gke.io"]
  resources: ["bundlebuilders", "bundles", "clusterbundles", "componentbuilders", "componentlists", "components", "componentsets", "gkeonprembundles", "packagedeploymentclasses", "packagedeployments", "patchtemplatebuilders", "patchtemplates", "requirements"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["bundleext.gke.io"]
  resources: ["nodeconfigs"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["certificates.k8s.io"]
  resources: ["certificatesigningrequests"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["cert-manager.io"]
  resources: ["certificaterequests", "certificates", "clusterissuers", "issuers"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["cilium.io"]
  resources: ["ciliumnodes", "ciliumendpoints", "ciliumidentities"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["configmanagement.gke.io"]
  resources: ["configmanagements"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["coordination.k8s.io"]
  resources: ["leases"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["cluster.k8s.io"]
  resources: ["clusters", "controlplanes", "machineclasses", "machinedeployments", "machines", "machinesets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["cluster.x-k8s.io"]
  resources: ["clusters", "controlplanes", "machineclasses", "machinedeployments", "machines", "machinesets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["crd.projectcalico.org"]
  resources: ["bgpconfigurations", "bgppeers", "blockaffinities", "clusterinformations", "felixconfigurations", "globalnetworkpolicies", "globalnetworksets", "hostendpoints", "ipamblocks", "ipamconfigs", "ipamhandles", "ippools", "networkpolicies", "networksets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["discovery.k8s.io"]
  resources: ["endpointslices"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["infrastructure.baremetal.cluster.gke.io"]
  resources: ["baremetalclusters", "baremetalmachines"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["networking.gke.io"]
  resources: ["bgpadvertisedroutes", "bgploadbalancers", "bgppeers", "bgpreceivedroutes", "bgpsessions", "clustercidrconfigs", "clusterdns", "egressnatpolicies"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingressclasses", "ingresses"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["node.k8s.io"]
  resources: ["runtimeclasses"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["onprem.cluster.gke.io"]
  resources: ["onpremadminclusters", "onpremnodepools", "onpremuserclusters", "validations", "onpremplatforms", "onprembundles", "clusterstates"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["policy"]
  resources: ["poddisruptionbudgets", "podsecuritypolicies"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterroles", "clusterrolebindings", "roles", "rolebindings"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["storage.k8s.io"]
  resources: ["csidrivers", "csinodes", "csistoragecapacities", "storageclasses", "volumeattachments"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["sriovnetwork.k8s.cni.cncf.io"]
  resources: ["sriovnetworknodepolicies", "sriovnetworknodestates", "sriovoperatorconfigs"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["vm.cluster.gke.io"]
  resources: ["gpuallocation", "guestenvironmentdata", "virtualmachineaccessrequest", "virtualmachinedisk", "virtualmachinepasswordresetrequest", "virtualmachinetype", "vmhighavailabilitypolicy", "vmruntime"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["vsphereproviderconfig.k8s.io"]
  resources: ["vsphereclusterproviderconfigs", "vspheremachineproviderconfigs"]
  verbs: ["get", "list", "watch"]
- apiGroups:
  - '*'
  resources: ["componentstatuses", "configmaps", "endpoints", "events", "horizontalpodautoscalers", "limitranges", "namespaces", "nodes", "persistentvolumeclaims", "persistentvolumes", "pods", "pods/log", "podtemplates", "replicationcontrollers", "resourcequotas", "serviceaccounts", "services"]
  verbs: ["get", "list", "watch"]
- nonResourceURLs:
  - '*'
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: gateway-anthos-support-permission-{metadata_name}
  labels:
    connect.gke.io/owner-feature: connect-gateway
subjects:{users}
roleRef:
  kind: ClusterRole
  name: anthos-support-reader
  apiGroup: rbac.authorization.k8s.io
---
"""


def ValidateRole(role):
  """Validation for the role in correct format."""
  cluster_pattern = re.compile('^clusterrole/')
  namespace_pattern = re.compile('^role/')
  if cluster_pattern.match(role.lower()):
    log.status.Print('Specified Cluster Role is:', role)
    if len(role.split('/')) != 2:
      raise InvalidArgsError(
          'Cluster role is not specified in correct format. Please specify the '
          'cluster role as: clusterrole/cluster-permission.'
      )
  elif namespace_pattern.match(role.lower()):
    log.status.Print('Specified Namespace Role is:', role)
    if len(role.split('/')) != 3:
      raise InvalidArgsError(
          'Namespace role is not specified in correct format. Please specify '
          'the namespace role as: role/namespace/namespace-permission'
      )
  else:
    raise InvalidArgsError(
        'The required role is not a cluster role or a namespace role.'
    )


def FormatIdentityForResourceNaming(identity, is_user):
  """Format user by removing disallowed characters for k8s resource naming."""
  # Check if the identity is a user or group.
  if is_user:
    desired_format = PRINCIPAL_USER_FORMAT
    error_message = INVALID_ARGS_USER_MESSAGE
  else:
    desired_format = PRINCIPAL_GROUP_FORMAT
    error_message = INVALID_ARGS_GROUP_MESSAGE
  parts = identity.split('/')
  if len(parts) >= 9:
    # Check the fields shared by all third-party principals.
    common_parts = parts[:4] + parts[5:8:2]
    if common_parts == desired_format:
      workforce_pool = identity.split('/workforcePools/')[1].split('/')[0]
      principal = identity.split('/{}/'.format(desired_format[-1]))[1]
      # Include workforce pool and remove unwanted characters from the
      # principal name.
      resource_name = workforce_pool + '_' + principal
    else:
      raise InvalidArgsError(error_message)
  else:
    if '@' not in identity:
      raise InvalidArgsError(error_message)
    else:
      resource_name = identity.split('@')[0]
  # Get rid of spaces to make RBAC policy management easier (not using
  # quotes around the name) and '/' and '%' due to naming restrictions.
  for ch in UNWANTED_CHARS:
    resource_name = resource_name.replace(ch, '')

  return resource_name


def ValidateArgs(args):
  """Validate Args in correct format."""
  # Validate the confliction between '--anthos-support' and '--role'.
  if not args.revoke and (
      (args.anthos_support and args.role)
      or (not args.anthos_support and not args.role)
  ):
    raise InvalidArgsError(
        'Please specify either --role or --anthos-support in the flags.'
    )
  if args.role:
    ValidateRole(args.role)
  # Validate either users/anthos-support or groups is set.
  if not args.users and not args.groups and not args.anthos_support:
    raise InvalidArgsError(
        'Please specify --groups: (--anthos-support --users) in flags.'
    )
  # Validate required flags when apply RBAC policy to cluster.
  if args.apply:
    if not args.membership:
      raise InvalidArgsError('Please specify the --membership in flags.')
    if not args.kubeconfig:
      raise InvalidArgsError('Please specify the --kubeconfig in flags.')
    if not args.context:
      raise InvalidArgsError('Please specify the --context in flags.')
  if args.revoke and args.apply:
    # Validate confliction between --apply and --revoke.
    raise InvalidArgsError(
        'Please specify either --apply or --revoke in flags.'
    )
  if args.revoke:
    # Validate required flags when revoke RBAC policy for specified user from
    # from cluster.
    if not args.membership:
      raise InvalidArgsError('Please specify the --membership in flags.')
    if not args.kubeconfig:
      raise InvalidArgsError('Please specify the --kubeconfig in flags.')
    if not args.context:
      raise InvalidArgsError('Please specify the --context in flags.')


def GetAnthosSupportUser(project_id):
  """Get P4SA account name for Anthos Support when user not specified."""
  project_number = projects_api.Get(
      projects_util.ParseProject(project_id)
  ).projectNumber
  hub_endpoint_override = hub_util.APIEndpoint()
  if hub_endpoint_override == hub_util.PROD_API:
    return ANTHOS_SUPPORT_USER.format(
        project_number=project_number, instance_name=''
    )
  elif hub_endpoint_override == hub_util.STAGING_API:
    return ANTHOS_SUPPORT_USER.format(
        project_number=project_number, instance_name='staging-'
    )
  elif hub_endpoint_override == hub_util.AUTOPUSH_API:
    return ANTHOS_SUPPORT_USER.format(
        project_number=project_number, instance_name='autopush-'
    )
  else:
    raise memberships_errors.UnknownApiEndpointOverrideError('gkehub')


def GenerateRBAC(args, project_id):
  """Returns the generated RBAC policy file with args provided."""
  generated_rbac = {}
  cluster_pattern = re.compile('^clusterrole/')
  namespace_pattern = re.compile('^role/')
  role_permission = ''
  rbac_policy_format = ''
  namespace = ''
  metadata_name = ''
  users_list = list()
  groups_list = list()

  if args.anthos_support:
    rbac_policy_format = (
        IMPERSONATE_POLICY_FORMAT + PERMISSION_POLICY_ANTHOS_SUPPORT_FORMAT
    )
  elif cluster_pattern.match(args.role.lower()):
    role_permission = args.role.split('/')[1]
    if args.users:
      rbac_policy_format = (
          IMPERSONATE_POLICY_FORMAT + PERMISSION_POLICY_CLUSTER_FORMAT
      )
    elif args.groups:
      rbac_policy_format = PERMISSION_POLICY_CLUSTER_FORMAT
  elif namespace_pattern.match(args.role.lower()):
    namespace = args.role.split('/')[1]
    role_permission = args.role.split('/')[2]
    if args.users:
      rbac_policy_format = (
          IMPERSONATE_POLICY_FORMAT + PERMISSION_POLICY_NAMESPACE_FORMAT
      )
    elif args.groups:
      rbac_policy_format = PERMISSION_POLICY_NAMESPACE_FORMAT
  else:
    raise InvalidArgsError(
        'Invalid flags, please specify either the --role or --anthos-support in'
        'your flags.'
    )

  if args.users:
    users_list = args.users.split(',')
  elif args.anthos_support:
    users_list.append(GetAnthosSupportUser(project_id))
  for user in users_list:
    impersonate_users = os.linesep + '  - {user}'.format(user=user)
    permission_users = os.linesep + '- kind: User'
    permission_users += os.linesep + '  name: {user}'.format(user=user)
    if args.membership:
      metadata_name = (
          project_id
          + '_'
          + FormatIdentityForResourceNaming(user, True)
          + '_'
          + args.membership
      )
    else:
      metadata_name = (
          project_id + '_' + FormatIdentityForResourceNaming(user, True)
      )

    # Assign value to the RBAC file templates.
    single_generated_rbac = rbac_policy_format.format(
        metadata_name=metadata_name,
        namespace=namespace,
        user_account=impersonate_users,
        users=permission_users,
        permission=role_permission,
    )
    generated_rbac[user] = single_generated_rbac

  if args.groups:
    groups_list = args.groups.split(',')
  for group in groups_list:
    permission_users = os.linesep + '- kind: Group'
    permission_users += os.linesep + '  name: {group}'.format(group=group)
    if args.membership:
      metadata_name = (
          project_id
          + '_'
          + FormatIdentityForResourceNaming(group, False)
          + '_'
          + args.membership
      )
    else:
      metadata_name = (
          project_id + '_' + FormatIdentityForResourceNaming(group, False)
      )

    # Assign value to the RBAC file templates.
    single_generated_rbac = rbac_policy_format.format(
        metadata_name=metadata_name,
        namespace=namespace,
        users=permission_users,
        permission=role_permission,
    )
    generated_rbac[group] = single_generated_rbac

  return generated_rbac


class InvalidArgsError(exceptions.Error):

  def __init__(self, error_message):
    message = '{}'.format(error_message)
    super(InvalidArgsError, self).__init__(message)
