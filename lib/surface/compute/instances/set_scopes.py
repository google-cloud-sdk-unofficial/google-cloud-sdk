# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Command to set scopes for an instance resource."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instances import exceptions
from googlecloudsdk.command_lib.compute.instances import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class SetScopes(base_classes.NoOutputAsyncMutator):
  """Set scopes and service account for a Google Compute Engine instance."""

  def __init__(self, *args, **kwargs):
    super(self.__class__, self).__init__(*args, **kwargs)
    self._instance = None

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser)
    flags.AddServiceAccountAndScopeArgs(parser, True)

  @property
  def method(self):
    return 'SetServiceAccount'

  @property
  def service(self):
    return self.compute.instances

  @property
  def resource_type(self):
    return 'instances'

  def _get_instance(self, instance_ref):
    """Return cached instance if there isn't one fetch referrenced one."""
    if self._instance:
      return self._instance

    errors = []
    request = (self.service, 'Get', self.messages.ComputeInstancesGetRequest(
        project=instance_ref.project,
        zone=instance_ref.zone,
        instance=instance_ref.instance))
    instance = list(request_helper.MakeRequests(
        requests=[request],
        http=self.http,
        batch_url=self.batch_url,
        errors=errors))
    if errors or not instance:
      raise exceptions.ResourceMissingException(
          'Instance {0} does not exist.'.format(instance_ref.SelfLink()))
    self._instance = instance[0]
    return self._instance

  def _original_email(self, instance_ref):
    """Return email of service account instance is using."""
    instance = self._get_instance(instance_ref)
    if instance is None:
      return None
    orignal_service_accounts = instance.serviceAccounts
    if orignal_service_accounts:
      return orignal_service_accounts[0].email
    return None

  def _original_scopes(self, instance_ref):
    """Return scopes instance is using."""
    instance = self._get_instance(instance_ref)
    if instance is None:
      return []
    orignal_service_accounts = instance.serviceAccounts
    result = []
    for accounts in orignal_service_accounts:
      result += accounts.scopes
    return result

  def _email(self, args, instance_ref):
    """Return email to set as service account for the instance."""
    if args.no_service_account:
      return None
    if args.service_account:
      return args.service_account
    return self._original_email(instance_ref)

  def _unprocessed_scopes(self, args, instance_ref):
    """Return scopes to set for the instance."""
    if args.no_scopes:
      return []
    if args.scopes:
      return args.scopes
    return self._original_scopes(instance_ref)

  def _scopes(self, args, instance_ref):
    """Get list of scopes to be assigned to the instance.

    Args:
      args: parsed command  line arguments.
      instance_ref: reference to the instance to which scopes will be assigned.

    Returns:
      List of scope urls extracted from args, with scope aliases expanded.
    """
    result = []
    for unprocessed_scope in self._unprocessed_scopes(args, instance_ref):
      scope = constants.SCOPES.get(unprocessed_scope, [unprocessed_scope])
      result.extend(scope)
    return result

  def CreateRequests(self, args):
    flags.ValidateServiceAccountAndScopeArgs(args)
    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args, self.resources,
        default_scope=compute_scope.ScopeEnum.ZONE,
        scope_lister=compute_flags.GetDefaultScopeLister(
            self.compute_client, self.project))

    email = self._email(args, instance_ref)
    scopes = self._scopes(args, instance_ref)

    if scopes and not email:
      raise exceptions.ScopesWithoutServiceAccountException(
          'Can not set scopes when there is no service acoount.')

    request = self.messages.ComputeInstancesSetServiceAccountRequest(
        instancesSetServiceAccountRequest=(
            self.messages.InstancesSetServiceAccountRequest(
                email=email,
                scopes=scopes,
            )
        ),
        project=self.project,
        zone=instance_ref.zone,
        instance=instance_ref.Name()
    )
    return [request]
