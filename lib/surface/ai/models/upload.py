# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to upload a model in AI platform."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.models import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import models_util
from googlecloudsdk.command_lib.ai import operations_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Upload(base.CreateCommand):
  """Upload a new model.

  Create a new AI Platform model.
  """

  @staticmethod
  def Args(parser):
    flags.AddUploadModelFlags(parser)

  def Run(self, args):
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    with endpoint_util.AiplatformEndpointOverrides(
        version=constants.BETA_VERSION, region=region):
      operation = client.ModelsClient().UploadV1Beta1(
          region_ref, args.display_name, args.description, args.artifact_uri,
          args.container_image_uri, args.container_command, args.container_args,
          args.container_env_vars, args.container_ports,
          args.container_predict_route, args.container_health_route)
      return operations_util.WaitForOpMaybe(
          operations_client=operations.OperationsClient(),
          op=operation,
          op_ref=models_util.ParseModelOperation(operation.name))
