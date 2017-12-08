# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Command for modifying backend services."""

from googlecloudsdk.api_lib.compute import backend_services_utils
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.core import resources


class InvalidResourceError(exceptions.ToolException):
  # Normally we'd want to subclass core.exceptions.Error, but base_classes.Edit
  # abuses ToolException to classify errors when displaying messages to users,
  # and we should continue to fit in that framework for now.
  pass


class Edit(base_classes.BaseEdit):
  """Modify backend services."""

  _BACKEND_SERVICE_ARG = flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG

  def __init__(self, *args, **kwargs):
    super(Edit, self).__init__(*args, **kwargs)
    self.ref = None

  @classmethod
  def Args(cls, parser):
    base_classes.BaseEdit.Args(parser)
    cls._BACKEND_SERVICE_ARG.AddArgument(parser)

  @property
  def service(self):
    if self.regional:
      return self.compute.regionBackendServices
    return self.compute.backendServices

  @property
  def resource_type(self):
    return 'backendServices'

  @property
  def example_resource(self):
    uri_prefix = ('https://www.googleapis.com/compute/v1/projects/'
                  'my-project/')
    instance_groups_uri_prefix = (
        'https://www.googleapis.com/compute/v1/projects/'
        'my-project/zones/')

    return self.messages.BackendService(
        backends=[
            self.messages.Backend(
                balancingMode=(
                    self.messages.Backend.BalancingModeValueValuesEnum.RATE),
                group=(
                    instance_groups_uri_prefix +
                    'us-central1-a/instanceGroups/group-1'),
                maxRate=100),
            self.messages.Backend(
                balancingMode=(
                    self.messages.Backend.BalancingModeValueValuesEnum.RATE),
                group=(
                    instance_groups_uri_prefix +
                    'europe-west1-a/instanceGroups/group-2'),
                maxRate=150),
        ],
        description='My backend service',
        healthChecks=[
            uri_prefix + 'global/httpHealthChecks/my-health-check-1',
            uri_prefix + 'global/httpHealthChecks/my-health-check-2'
        ],
        name='backend-service',
        port=80,
        portName='http',
        protocol=self.messages.BackendService.ProtocolValueValuesEnum.HTTP,
        selfLink=uri_prefix + 'global/backendServices/backend-service',
        timeoutSec=30,
    )

  def CreateReference(self, args):
    # TODO(b/35133484): remove once base classes are refactored away
    if not self.ref:
      self.ref = self._BACKEND_SERVICE_ARG.ResolveAsResource(
          args,
          self.resources,
          default_scope=backend_services_utils.GetDefaultScope(),
          scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client))
      self.regional = self.ref.Collection() == 'compute.regionBackendServices'
    return self.ref

  @property
  def reference_normalizers(self):

    def MakeReferenceNormalizer(field_name, allowed_collections):
      """Returns a function to normalize resource references."""
      def NormalizeReference(reference):
        """Returns normalized URI for field_name."""
        try:
          value_ref = self.resources.Parse(reference)
        except resources.UnknownCollectionException:
          raise InvalidResourceError(
              '[{field_name}] must be referenced using URIs.'.format(
                  field_name=field_name))

        if value_ref.Collection() not in allowed_collections:
          raise InvalidResourceError(
              'Invalid [{field_name}] reference: [{value}].'. format(
                  field_name=field_name, value=reference))
        return value_ref.SelfLink()
      return NormalizeReference

    # Ensure group is a uri or full collection path representing an instance
    # group. Full uris/paths are required because if the user gives us less, we
    # don't want to be in the business of guessing health checks.
    return [
        ('healthChecks[]',
         MakeReferenceNormalizer(
             'healthChecks',
             ('compute.httpHealthChecks', 'compute.httpsHealthChecks',
              'compute.healthChecks'))),
        ('backends[].group',
         MakeReferenceNormalizer(
             'group',
             ('compute.instanceGroups'))),
    ]

  def GetGetRequest(self, args):
    if self.regional:
      return (
          self.service,
          'Get',
          self.messages.ComputeRegionBackendServicesGetRequest(
              project=self.ref.project,
              region=self.ref.region,
              backendService=self.ref.Name()))
    return (
        self.service,
        'Get',
        self.messages.ComputeBackendServicesGetRequest(
            project=self.ref.project,
            backendService=self.ref.Name()))

  def GetSetRequest(self, args, replacement, _):
    if self.regional:
      return (
          self.service,
          'Update',
          self.messages.ComputeRegionBackendServicesUpdateRequest(
              project=self.ref.project,
              region=self.ref.region,
              backendService=self.ref.Name(),
              backendServiceResource=replacement))
    return (
        self.service,
        'Update',
        self.messages.ComputeBackendServicesUpdateRequest(
            project=self.ref.project,
            backendService=self.ref.Name(),
            backendServiceResource=replacement))


Edit.detailed_help = {
    'brief': 'Modify backend services',
    'DESCRIPTION': """\
        *{command}* can be used to modify a backend service. The backend
        service resource is fetched from the server and presented in a text
        editor. After the file is saved and closed, this command will
        update the resource. Only fields that can be modified are
        displayed in the editor.

        Backends are named by their associated instances groups, and one
        of the ``--group'' or ``--instance-group'' flags is required to
        identify the backend that you are modifying.  You cannot "change"
        the instance group associated with a backend, but you can accomplish
        something similar with ``backend-services remove-backend'' and
        ``backend-services add-backend''.

        The editor used to modify the resource is chosen by inspecting
        the ``EDITOR'' environment variable.
        """,
}
