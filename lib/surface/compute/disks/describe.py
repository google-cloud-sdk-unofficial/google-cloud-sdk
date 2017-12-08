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
"""Command for describing disks."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Describe(base_classes.ZonalDescriber):
  """Describe a Google Compute Engine disk."""

  @staticmethod
  def Args(parser):
    base_classes.ZonalDescriber.Args(parser, 'compute.disks')

  @property
  def service(self):
    return self.compute.disks

  @property
  def resource_type(self):
    return 'disks'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(base_classes.MultiScopeDescriber):
  """Describe a Google Compute Engine disk."""

  @staticmethod
  def Args(parser):
    base_classes.MultiScopeDescriber.AddScopeArgs(
        parser,
        'compute.disks',
        scope_types=[base_classes.ScopeType.zonal_scope,
                     base_classes.ScopeType.regional_scope])

  @property
  def global_service(self):
    """The service used to list global resources."""
    raise NotImplementedError()

  @property
  def regional_service(self):
    """The service used to list regional resources."""
    return self.compute.regionDisks

  @property
  def zonal_service(self):
    """The service used to list regional resources."""
    return self.compute.disks

  @property
  def global_resource_type(self):
    """The type of global resources."""
    return None

  @property
  def regional_resource_type(self):
    """The type of regional resources."""
    return 'regionDisks'

  @property
  def zonal_resource_type(self):
    """The type of regional resources."""
    return 'disks'


Describe.detailed_help = {
    'brief': 'Describe a Google Compute Engine disk',
    'DESCRIPTION': """\
        *{command}* displays all data associated with a Google Compute
        Engine disk in a project.
        """,
}

DescribeAlpha.detailed_help = Describe.detailed_help
