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
"""Init command for orchestration pipelines."""

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.orchestration_pipelines import scaffolding


@calliope_base.Hidden
@calliope_base.DefaultUniverseOnly
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
class Init(calliope_base.Command):
  """Initialize an orchestration pipeline."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'pipeline_name',
        nargs='?',
        default='orchestration-pipeline',
        help='The name of the pipeline file.',
    )
    parser.add_argument(
        '--environment',
        required=True,
        help='The environment name (e.g., dev, staging, prod).',
    )
    parser.add_argument(
        '--project',
        help='The Google Cloud project ID.',
    )
    parser.add_argument(
        '--region',
        help='The Google Cloud region.',
    )
    parser.add_argument(
        '--composer-environment',
        help='The Cloud Composer environment.',
    )
    parser.add_argument(
        '--artifacts-bucket',
        help='The Cloud Storage bucket for artifacts.',
    )
    parser.add_argument(
        '--service-account',
        help='The service account to use for the Composer environment.',
    )

  def Run(self, args):
    scaffolding.InitProject(args)
