# Copyright 2015 Google Inc. All Rights Reserved.
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
"""managed-instance-groups list-instances command.

It's an alias for the instance-groups list-instances command.
"""
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListInstances(instance_groups_utils.InstanceGroupListInstancesBase):
  """List Google Compute Engine instances present in managed instance group."""

  @staticmethod
  def Args(parser):
    instance_groups_utils.InstanceGroupListInstancesBase.ListInstancesArgs(
        parser, multizonal=False)

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroups'

  @property
  def method(self):
    return 'ListManagedInstances'

  @property
  def list_field(self):
    return 'managedInstances'

  def CreateGroupReference(self, args):
    return self.CreateZonalReference(args.name, args.zone)

  def GetResources(self, args):
    """Retrieves response with instance in the instance group."""
    group_ref = self.CreateZonalReference(args.name, args.zone)

    request = self.service.GetRequestType(self.method)(
        instanceGroupManager=group_ref.Name(),
        zone=group_ref.zone,
        project=group_ref.project)

    errors = []
    results = list(request_helper.MakeRequests(
        requests=[(self.service, self.method, request)],
        http=self.http,
        batch_url=self.batch_url,
        errors=errors,
        custom_get_requests=None))

    return results, errors

  def Format(self, args):
    return """\
        table(instance.basename():label=NAME,
              instanceStatus:label=STATUS,
              currentAction:label=ACTION,
              lastAttempt.errors.errors.map().format(
                "Error {0}: {1}", code, message).list(separator=", ")
                :label=LAST_ERROR
        )"""

  detailed_help = {
      'brief': 'List instances present in the managed instance group',
      'DESCRIPTION': """\
          *{command}* list instances in a managed instance group.
          """,
  }


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListInstancesBeta(ListInstances):
  """List Google Compute Engine instances present in managed instance group."""

  @staticmethod
  def Args(parser):
    instance_groups_utils.InstanceGroupListInstancesBase.ListInstancesArgs(
        parser, multizonal=True)

  def CreateGroupReference(self, args):
    return instance_groups_utils.CreateInstanceGroupReference(
        scope_prompter=self, compute=self.compute, resources=self.resources,
        name=args.name, region=args.region, zone=args.zone)

  def GetResources(self, args):
    """Retrieves response with instance in the instance group."""
    group_ref = self.CreateGroupReference(args)

    if hasattr(group_ref, 'zone'):
      service = self.compute.instanceGroupManagers
      request = service.GetRequestType(self.method)(
          instanceGroupManager=group_ref.Name(),
          zone=group_ref.zone,
          project=group_ref.project)
    elif hasattr(group_ref, 'region'):
      service = self.compute.regionInstanceGroupManagers
      request = service.GetRequestType(self.method)(
          instanceGroupManager=group_ref.Name(),
          region=group_ref.region,
          project=group_ref.project)

    errors = []
    results = list(request_helper.MakeRequests(
        requests=[(service, self.method, request)],
        http=self.http,
        batch_url=self.batch_url,
        errors=errors,
        custom_get_requests=None))

    return results, errors

  def Format(self, args):
    return """\
        table(instance.basename():label=NAME,
              instance.scope().segment(0):label=ZONE,
              instanceStatus:label=STATUS,
              currentAction:label=ACTION,
              lastAttempt.errors.errors.map().format(
                "Error {0}: {1}", code, message).list(separator=", ")
                :label=LAST_ERROR
        )"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListInstancesAlpha(ListInstancesBeta):
  """List Google Compute Engine instances present in managed instance group."""

  @staticmethod
  def Args(parser):
    instance_groups_utils.InstanceGroupListInstancesBase.ListInstancesArgs(
        parser, multizonal=True)

  def Format(self, args):
    return """\
        table(instance.basename():label=NAME,
              instance.scope().segment(0):label=ZONE,
              extract(instanceStatus, standbyMode).join('-'):label=STATUS,
              currentAction:label=ACTION,
              instanceTemplate.basename():label=INSTANCE_TEMPLATE,
              lastAttempt.errors.errors.map().format("Error {0}: {1}", code, message).list(separator=", "):label=LAST_ERROR
        )"""

ListInstancesBeta.detailed_help = ListInstances.detailed_help
ListInstancesAlpha.detailed_help = ListInstances.detailed_help
