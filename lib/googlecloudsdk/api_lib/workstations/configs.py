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
"""Cloud Workstations configs API utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.api_lib.workstations.util import GetClientInstance
from googlecloudsdk.api_lib.workstations.util import GetMessagesModule
from googlecloudsdk.api_lib.workstations.util import VERSION_MAP
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

IMAGE_URL_MAP = {
    'codeoss':
        'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest',
    'intellij':
        'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/intellij-ultimate:latest',
    'pycharm':
        'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/pycharm:latest',
    'rider':
        'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/rider:latest',
    'webstorm':
        'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/webstorm:latest',
    'phpstorm':
        'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/phpstorm:latest',
    'rubymine':
        'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/rubymine:latest',
    'goland':
        'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/goland:latest',
    'clion':
        'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/clion:latest',
    'base-image':
        'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/base:latest',
}


class Configs:
  """The Configs set of Cloud Workstations API functions."""

  def __init__(self, release_track=base.ReleaseTrack.BETA):
    self.api_version = VERSION_MAP.get(release_track)
    self.client = GetClientInstance(release_track)
    self.messages = GetMessagesModule(release_track)
    self._service = self.client.projects_locations_workstationClusters_workstationConfigs

  def Create(self, args):
    """Create a new workstation configuration.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Workstation configuration that was created.
    """
    config_name = args.CONCEPTS.config.Parse().RelativeName()
    parent = config_name.split('/workstationConfigs/')[0]
    config_id = config_name.split('/workstationConfigs/')[1]

    config = self.messages.WorkstationConfig()
    config.name = config_name
    config.idleTimeout = '{}s'.format(args.idle_timeout)
    config.runningTimeout = '{}s'.format(args.running_timeout)

    # GCE Instance Config
    config.host = self.messages.Host()
    config.host.gceInstance = self.messages.GceInstance()
    config.host.gceInstance.machineType = args.machine_type
    config.host.gceInstance.serviceAccount = args.service_account
    if args.network_tags:
      config.host.gceInstance.tags = args.network_tags
    config.host.gceInstance.poolSize = args.pool_size
    config.host.gceInstance.disablePublicIpAddresses = args.disable_public_ip_addresses
    config.host.gceInstance.shieldedInstanceConfig = self.messages.GceShieldedInstanceConfig(
        enableSecureBoot=args.shielded_secure_boot,
        enableVtpm=args.shielded_vtpm,
        enableIntegrityMonitoring=args.shielded_integrity_monitoring,
    )
    config.host.gceInstance.confidentialInstanceConfig = self.messages.GceConfidentialInstanceConfig(
        enableConfidentialCompute=args.enable_confidential_compute)
    config.host.gceInstance.bootDiskSizeGb = args.boot_disk_size

    # Persistent directory
    pd = self.messages.PersistentDirectory()
    pd.mountPath = '/home'
    if args.pd_reclaim_policy == 'retain':
      reclaim_policy = self.messages.GceRegionalPersistentDisk.ReclaimPolicyValueValuesEnum.RETAIN
    else:
      reclaim_policy = self.messages.GceRegionalPersistentDisk.ReclaimPolicyValueValuesEnum.DELETE

    pd.gcePd = self.messages.GceRegionalPersistentDisk(
        sizeGb=args.pd_disk_size,
        fsType='ext4',
        diskType=args.pd_disk_type,
        reclaimPolicy=reclaim_policy,
    )
    config.persistentDirectories.append(pd)

    # Container
    config.container = self.messages.Container()
    if args.container_custom_image:
      config.container.image = args.container_custom_image
    elif args.container_predefined_image:
      config.container.image = IMAGE_URL_MAP.get(
          args.container_predefined_image)
    if args.container_command:
      config.container.command = args.container_command
    if args.container_args:
      config.container.args = args.container_args
    if args.container_env:
      env_val = self.messages.Container.EnvValue()
      for key, value in args.container_env.items():
        env_val.additionalProperties.append(
            self.messages.Container.EnvValue.AdditionalProperty(
                key=key, value=value))
      config.container.env = env_val
    config.container.workingDir = args.container_working_dir
    config.container.runAsUser = args.container_run_as_user

    create_req = self.messages.WorkstationsProjectsLocationsWorkstationClustersWorkstationConfigsCreateRequest(
        parent=parent, workstationConfigId=config_id, workstationConfig=config)
    op_ref = self._service.Create(create_req)

    log.status.Print('Create request issued for: [{}]'.format(config_id))

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='workstations.projects.locations.operations',
        api_version=self.api_version)
    poller = waiter.CloudOperationPoller(
        self._service, self.client.projects_locations_operations)

    result = waiter.WaitFor(
        poller, op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name))
    log.status.Print('Created configuration [{}].'.format(config_id))

    return result
