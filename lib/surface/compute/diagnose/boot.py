# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Analyze VM serial console output for boot issues."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import ssh_troubleshooter_utils
from googlecloudsdk.command_lib.compute import vm_boot_troubleshooter
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log

MESSAGES = apis.GetMessagesModule('compute', 'alpha')


class BootDiagnosticError(core_exceptions.Error):
  """Base exception for boot diagnostic commands."""
  pass


def _IsInstanceWindows(instance):
  """Checks if the instance is a Windows instance.

  Args:
    instance: The instance resource object.

  Returns:
    bool: True if the instance is Windows.

  Raises:
    BootDiagnosticError: If the instance has no boot disk.
  """
  boot_disks = [disk for disk in (instance.disks or []) if disk.boot]
  if not boot_disks:
    raise BootDiagnosticError(
        'Instance [{0}] has no boot disk.'.format(instance.name)
    )
  if len(boot_disks) > 1:
    log.warning(
        'Multiple boot disks found for instance [{0}]. Using the first one.'
        .format(instance.name)
    )
  boot_disk = boot_disks[0]
  guest_os_features = boot_disk.guestOsFeatures or []
  features = [feature.type for feature in guest_os_features]
  return MESSAGES.GuestOsFeature.TypeValueValuesEnum.WINDOWS in features


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Boot(base_classes.BaseCommand):
  """Analyze a VM's serial console output for boot issues.

  {command} analyzes the serial console output of a Compute Engine
  virtual machine instance to detect boot issues.

  This command is currently only supported for Linux instances.
  """

  detailed_help = {
      'DESCRIPTION': """\
          *{command}* analyzes the serial console output of a Compute Engine
          virtual machine instance to detect boot issues.

          This command is currently only supported for Linux instances.
          """,
      'EXAMPLES': """\
          To analyze the boot logs of an instance named 'my-instance' in zone 'us-central1-a', run:

            $ {command} my-instance --zone=us-central1-a
          """,
  }

  @classmethod
  def Args(cls, parser):
    instance_flags.INSTANCE_ARG.AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resources = holder.resources

    instance_ref = instance_flags.INSTANCE_ARG.ResolveAsResource(
        args,
        resources,
        scope_lister=instance_flags.GetInstanceZoneScopeLister(client))

    self.instance_name = instance_ref.Name()

    # Fetch instance to check status
    try:
      instance = client.MakeRequests([(
          client.apitools_client.instances,
          'Get',
          client.messages.ComputeInstancesGetRequest(
              instance=self.instance_name,
              project=instance_ref.project,
              zone=instance_ref.zone,
          ),
      )])[0]
    except Exception as e:
      msg = 'Failed to get instance [{0}]: {1}'.format(
          self.instance_name, str(e))
      raise BootDiagnosticError(msg) from e

    # Check status
    if _IsInstanceWindows(instance):
      raise BootDiagnosticError(
          'Instance [{0}] is a Windows instance. This command currently '
          'supports Linux instances only.'.format(self.instance_name))

    if instance.status != MESSAGES.Instance.StatusValueValuesEnum.RUNNING:
      raise BootDiagnosticError(
          'Instance [{0}] is not running (status is {1}). '
          'Please start the instance to diagnose boot issues.'.format(
              self.instance_name, instance.status))

    # Pre-flight check: Try to fetch serial log to handle disabled logging and
    # empty buffer early
    log.status.Print(
        'Checking boot status for [{0}]...'.format(self.instance_name))
    try:
      sc_log = ssh_troubleshooter_utils.GetSerialConsoleLog(
          client.apitools_client, MESSAGES, self.instance_name,
          instance_ref.project, instance_ref.zone)
    except apitools_exceptions.HttpError as e:
      raise BootDiagnosticError(
          'Failed to retrieve serial port output. Please ensure that '
          'serial port logging is enabled for instance [{0}]. '
          'Error: {1}'.format(self.instance_name, str(e))) from e

    if not sc_log:
      raise BootDiagnosticError(
          'Serial console output for [{0}] is empty. '
          'If the instance was recently started, '
          'try again in a few moments.'.format(self.instance_name))

    project_obj = MESSAGES.Project(name=instance_ref.project)
    troubleshooter = vm_boot_troubleshooter.VMBootTroubleshooter(
        project_obj, instance_ref.zone, instance)

    return troubleshooter.FindBootIssues(sc_log=sc_log)

  def Display(self, args, resources):
    # resources is the list of BootFinding returned from Run
    if not resources:
      log.out.Print(
          'No boot issues detected for [{0}].'.format(self.instance_name))
      return

    for finding in resources:
      log.out.Print(finding.message.strip())
