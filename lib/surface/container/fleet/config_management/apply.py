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
"""The command to update Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.config_management import utils
from googlecloudsdk.command_lib.container.fleet.features import base as fleet_base
from googlecloudsdk.command_lib.container.fleet.policycontroller import constants
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml

# Pull out the example text so the example command can be one line without the
# py linter complaining. The docgen tool properly breaks it into multiple lines.
EXAMPLES = r"""
    To apply a YAML config file to a membership, prepare
    [apply-spec.yaml](https://cloud.google.com/anthos-config-management/docs/reference/gcloud-apply-fields#example_gcloud_apply_spec) then run:

      $ {command} --membership=MEMBERSHIP_NAME --config=APPLY-SPEC.YAML --version=VERSION
"""
# TODO(b/298461043): Move error message instructions into
# https://cloud.google.com/anthos-config-management/docs/reference/gcloud-apply-fields.
MAP_NODE_EXCEPTION_FORMAT = ('{} must be a YAML mapping node.'
                             ' This field should either contain indented'
                             ' key, value pairs or have the empty map {{}} as'
                             ' its value.'
                             ' See --help flag output for links to examples.')


@base.DefaultUniverseOnly
class Apply(fleet_base.UpdateCommand):
  """Update a Config Management Feature Spec.

  Update a user-specified config file to a ConfigManagement Custom Resource.
  The config file should be a .yaml file, all eligible fields are listed in
  https://cloud.google.com/anthos-config-management/docs/reference/gcloud-apply-fields
  """

  detailed_help = {'EXAMPLES': EXAMPLES}

  feature_name = 'configmanagement'

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(parser)
    parser.add_argument(
        '--config',
        type=str,
        help='The path to config-management.yaml.',
        required=True,
    )
    parser.add_argument(
        '--version', type=str, help='The version of ACM to install.'
    )

  def Run(self, args):
    utils.enable_poco_api_if_disabled(self.Project())

    # check static yaml fields before query membership
    # TODO(b/298461043): Investigate whether it is worth our time to move the
    # apply-spec syntax into proto so that we get automatic parsing.
    try:
      loaded_cm = yaml.load_path(args.config)
    except yaml.Error as e:
      raise exceptions.Error(
          'Invalid config yaml file {}'.format(args.config), e
      )
    _validate_meta(loaded_cm)

    membership = fleet_base.ParseMembership(
        args, prompt=True, autoselect=True, search=True
    )

    # TODO(b/298461043): Scan for illegal fields by reading from
    # utils.APPLY_SPEC_VERSION_1. Access specific fields via constant variables
    # in utils.
    config_sync = _parse_config_sync(loaded_cm, self.messages)
    policy_controller = _parse_policy_controller(loaded_cm, self.messages)
    hierarchy_controller_config = _parse_hierarchy_controller_config(
        loaded_cm, self.messages
    )

    upgrades = loaded_cm.get('spec', {}).get(utils.UPGRADES, '')
    validate_upgrades(upgrades)
    version = args.version
    if upgrades != utils.UPGRADES_AUTO and not version:
      version = self._get_backfill_version(membership)
    cluster = loaded_cm.get('spec', {}).get('cluster', '')
    spec = self.messages.MembershipFeatureSpec(
        configmanagement=self.messages.ConfigManagementMembershipSpec(
            version=version,
            cluster=cluster,
            management=self.upgradesFromStr(upgrades),
            configSync=config_sync,
            policyController=policy_controller,
            hierarchyController=hierarchy_controller_config,
        )
    )
    spec_map = {membership: spec}

    # UpdateFeature uses patch method to update membership_configs map,
    # there's no need to get the existing feature spec
    patch = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(spec_map)
    )
    self.Update(['membership_specs'], patch)

  def upgradesFromStr(self, upgrades):
    """Convert the string `upgrades` to an enum in the ACM Fleet Feature API.

    Args:
      upgrades: a string.

    Returns:
      an enum represent the field `management` in the ACM Fleet Feature API.
    """
    if upgrades == utils.UPGRADES_AUTO:
      return self.messages.ConfigManagementMembershipSpec.ManagementValueValuesEnum(
          utils.MANAGEMENT_AUTOMATIC
      )
    else:
      return self.messages.ConfigManagementMembershipSpec.ManagementValueValuesEnum(
          utils.MANAGEMENT_MANUAL
      )

  def _get_backfill_version(self, membership):
    """Get the value the version field in FeatureSpec should be set to.

    Args:
      membership: The full membership  name whose Spec will be backfilled.

    Returns:
      version: A string denoting the version field in MembershipConfig
    Raises: Error, if retrieving FeatureSpec of FeatureState fails
    """
    f = self.GetFeature()
    return utils.get_backfill_version_from_feature(f, membership)


def validate_upgrades(upgrades):
  """Validate the string `upgrades`.

  Args:
    upgrades: a string.

  Raises: Error, if upgrades is invalid.
  """
  legal_fields = [
      utils.UPGRADES_AUTO,
      utils.UPGRADES_MANUAL,
      utils.UPGRADES_EMPTY,
  ]
  valid_values = ' '.join(f"'{field}'" for field in legal_fields)
  if upgrades not in legal_fields:
    raise exceptions.Error(
        'The valid values of field .spec.{} are: {}'.format(
            utils.UPGRADES, valid_values
        )
    )


def _validate_meta(configmanagement):
  """Validate the parsed configmanagement yaml.

  Args:
    configmanagement: Data type loaded from yaml.
  Raises: gcloud core Error, if the top-level fields have invalid syntax.
  """
  if not isinstance(configmanagement, dict):
    raise exceptions.Error('Invalid ConfigManagement template.')
  illegal_root_fields = _find_unknown_fields(configmanagement, {
      'applySpecVersion',
      'spec',
  })
  if illegal_root_fields:
    raise exceptions.Error('Please remove illegal field(s) {}'.format(
        ', '.join(['.'+f for f in illegal_root_fields])
    ))
  # TODO(b/298461043): Document applySpecVersion better in
  # https://cloud.google.com/anthos-config-management/docs/reference/gcloud-apply-fields.
  if 'applySpecVersion' not in configmanagement:
    raise exceptions.Error('Missing required field .applySpecVersion')
  if configmanagement['applySpecVersion'] != 1:
    raise exceptions.Error(
        'Only "applySpecVersion: 1" is supported. To use a later version,'
        'please fetch the config by running\n'
        'gcloud container fleet config-management fetch-for-apply'
    )
  if 'spec' not in configmanagement:
    raise exceptions.Error('Missing required field .spec')
  if not isinstance(configmanagement['spec'], dict):
    raise exceptions.Error(MAP_NODE_EXCEPTION_FORMAT.format('.spec'))
  illegal_spec_fields = _find_unknown_fields(configmanagement['spec'], {
      utils.CONFIG_SYNC,
      utils.POLICY_CONTROLLER,
      utils.HNC,
      utils.CLUSTER,
      utils.UPGRADES,
  })
  if illegal_spec_fields:
    raise exceptions.Error('Please remove illegal field(s) {}'.format(
        ', '.join(['.spec.'+f for f in illegal_spec_fields])
    ))


def _parse_config_sync(configmanagement, msg):
  """Load ConfigSync configuration with the parsed configmanagement yaml.

  Args:
    configmanagement: dict, The data loaded from the config-management.yaml
      given by user.
    msg: The Hub messages package.

  Returns:
    config_sync: The ConfigSync configuration holds configmanagement.spec.git
    or configmanagement.spec.oci being used in MembershipConfigs
  Raises: gcloud core Error, if the configSync field on configmanagement has
    invalid syntax. Note that this function does not check semantic meaning of
    field values, other than for .spec.configSync.sourceType.
  """

  if (
      'spec' not in configmanagement
      or utils.CONFIG_SYNC not in configmanagement['spec']
  ):
    return None
  if not isinstance(configmanagement['spec'][utils.CONFIG_SYNC], dict):
    raise exceptions.Error(
        MAP_NODE_EXCEPTION_FORMAT.format('.spec.'+utils.CONFIG_SYNC)
    )
  spec_source = configmanagement['spec'][utils.CONFIG_SYNC]
  illegal_fields = _find_unknown_fields(spec_source,
                                        yaml.load(utils.APPLY_SPEC_VERSION_1)
                                        ['spec'][utils.CONFIG_SYNC])
  if illegal_fields:
    raise exceptions.Error('Please remove illegal field(s) {}'.format(', '.join(
        ['.spec.{}.{}'.format(utils.CONFIG_SYNC, f) for f in illegal_fields]
    )))

  config_sync = msg.ConfigManagementConfigSync()
  # missing `enabled: true` will enable configSync
  config_sync.enabled = True
  if 'enabled' in spec_source:
    config_sync.enabled = spec_source['enabled']
  # Default to use sourceType 'git' if not specified
  source_type = spec_source.get('sourceType', 'git')
  if source_type == 'git':
    config_sync.git = _parse_git_config(spec_source, msg)
  elif source_type == 'oci':
    config_sync.oci = _parse_oci_config(spec_source, msg)
  else:
    raise exceptions.Error((
        '.spec.{}.sourceType has illegal value {}.'
        ' Please replace with `git` or `oci`'.format(
            utils.CONFIG_SYNC, source_type
        )
    ))
  if 'sourceFormat' in spec_source:
    config_sync.sourceFormat = spec_source['sourceFormat']
  if 'preventDrift' in spec_source:
    config_sync.preventDrift = spec_source['preventDrift']
  if 'metricsGcpServiceAccountEmail' in spec_source:
    config_sync.metricsGcpServiceAccountEmail = spec_source[
        'metricsGcpServiceAccountEmail'
    ]

  return config_sync


def _parse_git_config(spec_source, msg):
  """Load GitConfig with the parsed config_sync yaml.

  Args:
    spec_source: The config_sync dict loaded from the config-management.yaml
      given by user.
    msg: The Hub messages package.

  Returns:
    git_config: The GitConfig configuration being used in MembershipConfigs
  """

  git_config = msg.ConfigManagementGitConfig()
  if 'syncWait' in spec_source:
    git_config.syncWaitSecs = spec_source['syncWait']
  for field in [
      'policyDir',
      'secretType',
      'syncBranch',
      'syncRepo',
      'syncRev',
      'httpsProxy',
      'gcpServiceAccountEmail',
  ]:
    if field in spec_source:
      setattr(git_config, field, spec_source[field])
  return git_config


def _parse_oci_config(spec_source, msg):
  """Load OciConfig with the parsed config_sync yaml.

  Args:
    spec_source: The config_sync dict loaded from the config-management.yaml
      given by user.
    msg: The Hub messages package.

  Returns:
    oci_config: The OciConfig being used in MembershipConfigs
  """

  oci_config = msg.ConfigManagementOciConfig()
  if 'syncWait' in spec_source:
    oci_config.syncWaitSecs = spec_source['syncWait']
  for field in [
      'policyDir',
      'secretType',
      'syncRepo',
      'gcpServiceAccountEmail',
  ]:
    if field in spec_source:
      setattr(oci_config, field, spec_source[field])
  return oci_config


def _parse_policy_controller(configmanagement, msg):
  """Load PolicyController with the parsed config-management.yaml.

  Args:
    configmanagement: dict, The data loaded from the config-management.yaml
      given by user.
    msg: The Hub messages package.

  Returns:
    policy_controller: The Policy Controller configuration for
    MembershipConfigs, filled in the data parsed from
    configmanagement.spec.policyController
  Raises: gcloud core Error, if Policy Controller has invalid syntax. Note that
    this function does not check semantic meaning of field values other than
    monitoring backends.
  """

  if (
      'spec' not in configmanagement
      or 'policyController' not in configmanagement['spec']
  ):
    return None

  if not isinstance(configmanagement['spec']['policyController'], dict):
    raise exceptions.Error(
        MAP_NODE_EXCEPTION_FORMAT.format('.spec.policyController')
    )
  spec_policy_controller = configmanagement['spec']['policyController']
  # Required field
  if 'enabled' not in spec_policy_controller:
    raise exceptions.Error(
        'Missing required field .spec.policyController.enabled'
    )
  enabled = spec_policy_controller['enabled']
  if not isinstance(enabled, bool):
    raise exceptions.Error(
        'policyController.enabled should be `true` or `false`'
    )

  policy_controller = msg.ConfigManagementPolicyController()
  # When the policyController is set to be enabled, policy_controller will
  # be filled with the valid fields set in spec_policy_controller, which
  # were mapped from the config-management.yaml
  illegal_fields = _find_unknown_fields(spec_policy_controller, {
      'enabled',
      'templateLibraryInstalled',
      'auditIntervalSeconds',
      'referentialRulesEnabled',
      'exemptableNamespaces',
      'logDeniesEnabled',
      'mutationEnabled',
      'monitoring',
  })
  if illegal_fields:
    raise exceptions.Error('Please remove illegal field(s) {}'.format(
        ', '.join(['.spec.policyController.'+f for f in illegal_fields])
    ))
  for field in spec_policy_controller:
    if field == 'monitoring':
      monitoring = _build_monitoring_msg(spec_policy_controller[field], msg)
      setattr(policy_controller, field, monitoring)
    else:
      setattr(policy_controller, field, spec_policy_controller[field])

  return policy_controller


def _parse_hierarchy_controller_config(configmanagement, msg):
  """Load HierarchyController with the parsed config-management.yaml.

  Args:
    configmanagement: dict, The data loaded from the config-management.yaml
      given by user.
    msg: The Hub messages package.

  Returns:
    hierarchy_controller: The Hierarchy Controller configuration for
    MembershipConfigs, filled in the data parsed from
    configmanagement.spec.hierarchyController
  Raises: gcloud core Error, if Hierarchy Controller has invalid syntax. Note
    that this function does not check semantic meaning of field values.
  """

  if (
      'spec' not in configmanagement
      or 'hierarchyController' not in configmanagement['spec']
  ):
    return None

  if not isinstance(configmanagement['spec']['hierarchyController'], dict):
    raise exceptions.Error(
        MAP_NODE_EXCEPTION_FORMAT.format('.spec.hierarchyController')
    )
  spec = configmanagement['spec']['hierarchyController']
  # Required field
  if 'enabled' not in spec:
    raise exceptions.Error(
        'Missing required field .spec.hierarchyController.enabled'
    )
  if not isinstance(spec['enabled'], bool):
    raise exceptions.Error(
        'hierarchyController.enabled should be `true` or `false`'
    )

  config_proto = msg.ConfigManagementHierarchyControllerConfig()
  # When the hierarchyController is set to be enabled, hierarchy_controller will
  # be filled with the valid fields set in spec, which
  # were mapped from the config-management.yaml
  illegal_fields = _find_unknown_fields(spec, {
      'enabled',
      'enablePodTreeLabels',
      'enableHierarchicalResourceQuota',
  })
  if illegal_fields:
    raise exceptions.Error('Please remove illegal field(s) {}'.format(
        ', '.join(['.spec.hierarchyController.'+f for f in illegal_fields])
    ))
  for field in spec:
    setattr(config_proto, field, spec[field])

  return config_proto


def _find_unknown_fields(source, known_fields):
  """Returns the list of string elements in source not in known_fields.

  Args:
    source: The source iterable to check.
    known_fields: The collection of known fields.
  """
  illegal_fields = []
  for field in source:
    if field not in known_fields:
      illegal_fields.append(field)
  return illegal_fields


def _build_monitoring_msg(spec_monitoring, msg):
  """Build PolicyControllerMonitoring message from the parsed spec.

  Args:
    spec_monitoring: dict, The monitoring data loaded from the
      config-management.yaml given by user.
    msg: The Hub messages package.

  Returns:
    monitoring: The Policy Controller Monitoring configuration for
    MembershipConfigs, filled in the data parsed from
    configmanagement.spec.policyController.monitoring
  Raises: gcloud core Error, if spec_monitoring is invalid, including its
    backend values.
  """
  if not isinstance(spec_monitoring, dict):
    raise exceptions.Error(
        MAP_NODE_EXCEPTION_FORMAT.format('.spec.policyController.monitoring')
    )
  backends = spec_monitoring.get('backends', [])
  if not backends:
    return None

  # n.b. Policy Controller is the source of truth for supported backends.
  converter = constants.monitoring_backend_converter(msg)

  def convert(backend):
    result = converter.get(backend.lower())
    if not result:
      raise exceptions.Error(
          'policyController.monitoring.backend {} is not recognized'.format(
              backend
          )
      )
    return result
  try:
    monitoring_backends = [convert(backend) for backend in backends]
  except (TypeError, AttributeError):
    raise exceptions.Error(
        ('.spec.policyController.monitoring.backend must be a sequence of'
         ' strings. See --help flag output for details')
    )
  monitoring = msg.ConfigManagementPolicyControllerMonitoring()
  monitoring.backends = monitoring_backends
  return monitoring
