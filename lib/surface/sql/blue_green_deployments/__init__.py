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
"""The command group for Cloud SQL blue-green deployments."""

from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class BlueGreenDeployments(base.Group):
  """Blue-green deployment is a strategy that minimizes database downtime when you make changes, like major version upgrades, by copying a production environment to a separate, synchronized staging environment.

  With blue-green deployments, you can make changes to a staging
  environment-the green environment-without affecting the production
  environment-the blue environment. When you're ready, you can switch over with
  low downtime, promoting the staging environment to be the new production
  environment.

  These commands help you manage the lifecycle of creating the green
  environment, testing, switching over, and cleaning up old resources in Cloud
  SQL.
  """
