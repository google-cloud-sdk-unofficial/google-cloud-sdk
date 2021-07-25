# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Export backend service command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import backend_services_utils
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.command_lib.util.declarative import python_command_util as declarative_python_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Export(base.Command):
  """Export the configuration for a backend service."""

  detailed_help = declarative_python_util.BuildHelpText(
      singular='backend service', service='Compute Engine')

  @classmethod
  def Args(cls, parser):
    declarative_python_util.RegisterArgs(
        parser,
        flags.GLOBAL_REGIONAL_BACKEND_SERVICE_NOT_REQUIRED_ARG.AddArgument,
        operation_type='export')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    (backend_services_utils
     .IsDefaultRegionalBackendServicePropertyNoneWarnOtherwise())
    resource_ref = str(
        flags.GLOBAL_REGIONAL_BACKEND_SERVICE_NOT_REQUIRED_ARG
        .ResolveAsResource(
            args,
            holder.resources,
            scope_lister=compute_flags.GetDefaultScopeLister(holder.client)))
    return declarative_python_util.RunExport(
        args=args,
        collection='compute.backendServices',
        resource_ref=resource_ref)
