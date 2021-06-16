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
"""The command to update Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.container.hub.config_management import utils
from googlecloudsdk.command_lib.container.hub.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io

MEMBERSHIP_FLAG = '--membership'
CONFIG_YAML_FLAG = '--config'
membership = None


class Apply(base.UpdateCommand):
  r"""Update a Config Management Feature Spec.

  Update a user-specified config file to a ConfigManagement Custom Resource.
  The config file should be a yaml file.

  ## Examples

  Apply ConfigManagement yaml file:

    $ {command} --membership=CLUSTER_NAME \
    --config=/path/to/config-management.yaml
  """

  feature_name = 'configmanagement'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        MEMBERSHIP_FLAG,
        type=str,
        help=textwrap.dedent("""\
            The Membership name provided during registration.
            """),
    )
    parser.add_argument(
        CONFIG_YAML_FLAG,
        type=str,
        help=textwrap.dedent("""\
            The path to config-management.yaml.
            """),
        required=True)

  def Run(self, args):
    # check static yaml fields before query membership
    try:
      loaded_cm = yaml.load_path(args.config)
    except yaml.Error as e:
      raise exceptions.Error(
          'Invalid config yaml file {}'.format(args.config), e)
    _validate_meta(loaded_cm)

    # make sure a valid membership is selected
    project = properties.VALUES.core.project.GetOrFail()
    memberships = base.ListMemberships(project)
    if not memberships:
      raise exceptions.Error('No Memberships available in Hub.')
    # User should choose an existing membership if not provide one
    global membership
    if not args.membership:
      index = console_io.PromptChoice(
          options=memberships,
          message='Please specify a membership to apply {}:\n'.format(
              args.config))
      membership = memberships[index]
    else:
      membership = args.membership
      if membership not in memberships:
        raise exceptions.Error(
            'Membership {} is not in Hub.'.format(membership))
    client = core_apis.GetClientInstance('gkehub', 'v1alpha1')
    msg = client.MESSAGES_MODULE
    config_sync = _parse_config_sync(loaded_cm, msg)
    policy_controller = _parse_policy_controller(loaded_cm, msg)
    hierarchy_controller_config = _parse_hierarchy_controller_config(
        loaded_cm, msg)
    applied_config = msg.ConfigManagementFeatureSpec.MembershipConfigsValue.AdditionalProperty(
        key=membership,
        value=msg.MembershipConfig(
            version=self._get_backfill_version(membership),
            configSync=config_sync,
            policyController=policy_controller,
            hierarchyController=hierarchy_controller_config))
    # UpdateFeature uses patch method to update membership_configs map,
    # there's no need to get the existing feature spec
    m_configs = msg.ConfigManagementFeatureSpec.MembershipConfigsValue(
        additionalProperties=[applied_config])
    self.RunCommand(
        'configmanagement_feature_spec.membership_configs',
        configmanagementFeatureSpec=msg.ConfigManagementFeatureSpec(
            membershipConfigs=m_configs))

  def _get_backfill_version(self, mem):
    """Get the value the version field in FeatureSpec should be set to.

    Args:
      mem: The membership name whose Spec will be backfilled.

    Returns:
      version: A string denoting the version field in MembershipConfig
    Raises: Error, if retrieving FeatureSpec of FeatureState fails
    """
    project_id = properties.VALUES.core.project.GetOrFail()
    response = utils.try_get_configmanagement(project_id)

    # First check FeatureSpec to see if an existing version is set
    mem_config = _parse_membership(response, mem)
    if mem_config and mem_config.version:
      return mem_config.version

    # Next, check FeatureState
    if response.featureState and response.featureState.detailsByMembership:
      membership_details = response.featureState.detailsByMembership.additionalProperties
      for m in membership_details:
        if os.path.basename(m.key) == mem:
          fs = m.value.configmanagementFeatureState
          if fs and fs.membershipConfig and fs.membershipConfig.version:
            # If the version on the cluster is later than the latest supported
            # version in the Hub API, we do not want to write this version to
            # spec. If we did, this would result in an error updating spec,
            # rendering this gcloud command unusable.
            return fs.membershipConfig.version \
              if fs.membershipConfig.version <= utils.LATEST_VERSION else ''

    # If Spec/State did not contain version, return default (latest version)
    return utils.LATEST_VERSION


def _parse_membership(response, mem):
  if response.configmanagementFeatureSpec is None or response.configmanagementFeatureSpec.membershipConfigs is None:
    return None

  for details in response.configmanagementFeatureSpec.membershipConfigs.additionalProperties:
    if details.key == mem:
      return details.value


def _validate_meta(configmanagement):
  """Validate the parsed configmanagement yaml.

  Args:
    configmanagement: The dict loaded from yaml.
  """
  if not isinstance(configmanagement, dict):
    raise exceptions.Error('Invalid ConfigManagement template.')
  if configmanagement.get('applySpecVersion') != 1:
    raise exceptions.Error(
        'Only "applySpecVersion: 1" is supported. To use a later version,'
        'please fetch the config by running\n'
        'g3cloud alpha container hub config-management fetch-for-apply')

  if 'spec' not in configmanagement:
    raise exceptions.Error('Missing required field .spec')
  spec = configmanagement['spec']
  for field in spec:
    if field not in [utils.CONFIG_SYNC, utils.POLICY_CONTROLLER, utils.HNC]:
      raise exceptions.Error(
          'Please remove illegal field .spec.{}'.format(field))


def _parse_config_sync(configmanagement, msg):
  """Load GitConfig with the parsed configmanagement yaml.

  Args:
    configmanagement: dict, The data loaded from the config-management.yaml
      given by user.
    msg: The empty message class for gkehub version v1alpha1
  Returns:
    config_sync: The ConfigSync configuration holds configmanagement.spec.git
    being used in MembershipConfigs
  Raises: Error, if required fields are missing from .spec.git
  """

  if ('spec' not in configmanagement or
      utils.CONFIG_SYNC not in configmanagement['spec']):
    return None
  spec_git = configmanagement['spec'][utils.CONFIG_SYNC]
  for field in spec_git:
    if field not in yaml.load(
        utils.APPLY_SPEC_VERSION_1)['spec'][utils.CONFIG_SYNC]:
      raise exceptions.Error(
          'The field .spec.{}.{}'.format(utils.CONFIG_SYNC, field) +
          ' is unrecognized in this applySpecVersion. Please remove.')
  git_config = msg.GitConfig()
  config_sync = msg.ConfigSync(git=git_config)
  # missing `enabled: true` will disable configSync
  if 'enabled' not in spec_git:
    raise exceptions.Error(
        'Missing required field [{}.enabled]'.format(utils.CONFIG_SYNC))
  if not spec_git['enabled']:
    return config_sync
  # https://cloud.google.com/anthos-config-management/docs/how-to/installing#configuring-git-repo
  # Required field
  for field in ['syncRepo', 'secretType']:
    if field not in spec_git:
      raise exceptions.Error('Missing required field [{}.{}].'.format(
          utils.CONFIG_SYNC, field))
  # TODO(b/189131417) remove git validation, catch the CLH result instead.
  valid_sf = ['hierarchy', 'unstructured']
  if 'sourceFormat' in spec_git and spec_git['sourceFormat'] not in valid_sf:
    raise exceptions.Error('Please fix unrecognized value of '
                           '.spec.{}.sourceFormat, only [{}] are supported'
                           .format(utils.CONFIG_SYNC, ','.join(valid_sf)))
  for field in [
      'policyDir', 'secretType', 'syncBranch', 'syncRepo', 'syncRev',
      'httpsProxy'
  ]:
    if field in spec_git:
      setattr(git_config, field, spec_git[field])
  if 'syncWait' in spec_git:
    git_config.syncWaitSecs = spec_git['syncWait']

  if 'sourceFormat' in spec_git:
    config_sync.sourceFormat = spec_git['sourceFormat']
  return config_sync


def _parse_policy_controller(configmanagement, msg):
  """Load PolicyController with the parsed config-management.yaml.

  Args:
    configmanagement: dict, The data loaded from the config-management.yaml
      given by user.
    msg: The empty message class for gkehub version v1alpha1
  Returns:
    policy_controller: The Policy Controller configuration for
    MembershipConfigs, filled in the data parsed from
    configmanagement.spec.policyController
  Raises: Error, if Policy Controller `enabled` is missing or not a boolean
  """

  if ('spec' not in configmanagement or
      'policyController' not in configmanagement['spec']):
    return None

  spec_policy_controller = configmanagement['spec']['policyController']
  # Required field
  if configmanagement['spec'][
      'policyController'] is None or 'enabled' not in spec_policy_controller:
    raise exceptions.Error(
        'Missing required field .spec.policyController.enabled')
  enabled = spec_policy_controller['enabled']
  if not isinstance(enabled, bool):
    raise exceptions.Error(
        'policyController.enabled should be `true` or `false`')

  policy_controller = msg.PolicyController()
  # When the policyController is set to be enabled, policy_controller will
  # be filled with the valid fields set in spec_policy_controller, which
  # were mapped from the config-management.yaml
  for field in spec_policy_controller:
    if field not in [
        'enabled', 'templateLibraryInstalled', 'auditIntervalSeconds',
        'referentialRulesEnabled', 'exemptableNamespaces', 'logDeniesEnabled'
    ]:
      raise exceptions.Error(
          'Please remove illegal field .spec.policyController.{}'.format(field))
    setattr(policy_controller, field, spec_policy_controller[field])

  return policy_controller


def _parse_hierarchy_controller_config(configmanagement, msg):
  """Load HierarchyController with the parsed config-management.yaml.

  Args:
    configmanagement: dict, The data loaded from the config-management.yaml
      given by user.
    msg: The empty message class for gkehub version v1alpha1

  Returns:
    hierarchy_controller: The Hierarchy Controller configuration for
    MembershipConfigs, filled in the data parsed from
    configmanagement.spec.hierarchyController
  Raises: Error, if Hierarchy Controller `enabled` set to false but also has
    other fields present in the config
  """

  if ('spec' not in configmanagement or
      'hierarchyController' not in configmanagement['spec']):
    return None

  spec = configmanagement['spec']['hierarchyController']
  # Required field
  if spec is None or 'enabled' not in spec:
    raise exceptions.Error(
        'Missing required field .spec.hierarchyController.enabled')
  enabled = spec['enabled']
  if not isinstance(enabled, bool):
    raise exceptions.Error(
        'hierarchyController.enabled should be `true` or `false`')

  config_proto = msg.HierarchyControllerConfig()
  # When the hierarchyController is set to be enabled, hierarchy_controller will
  # be filled with the valid fields set in spec, which
  # were mapped from the config-management.yaml
  for field in spec:
    if field not in [
        'enabled', 'enablePodTreeLabels', 'enableHierarchicalResourceQuota'
    ]:
      raise exceptions.Error(
          'Please remove illegal field .spec.hierarchyController{}'.format(
              field))
    setattr(config_proto, field, spec[field])

  return config_proto
