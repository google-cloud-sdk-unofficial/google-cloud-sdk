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
"""The unit-operations command group for the App Lifecycle Manager CLI."""

from googlecloudsdk.calliope import base


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Saas(base.Group):
  category = base.SAAS_CATEGORY
  detailed_help = {
      'brief': 'Manage App Lifecycle Manager unit operations.',
      'DESCRIPTION': """
          Manage App Lifecycle Manager unit operations. A unit operation
          encapsulates the intent to change or interact with the service
          component represented by a specific unit. For example, a unit
          operation can provision, upgrade, or deprovision the unit. Multiple
          unit operations can be requested and scheduled, but only one runs at
          a time.
      """,
      'EXAMPLES': """
          To create a unit operation named `my-unit-operation` in location
          `us-central1` that provisions the unit `my-unit` with the release
          `my-release`, run:

            $ {command} create my-unit-operation --location=us-central1 --unit=my-unit --provision --provision-release=my-release

          To list the names of all unit operations in location `us-central1`,
          run:

            $ {command} list --location=us-central1 --format="value(name)"

          To describe the unit operation named `my-unit-operation` in location
          `us-central1`, run:

            $ {command} describe my-unit-operation --location=us-central1
      """,
  }


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SaasAlpha(base.Group):
  category = base.SAAS_CATEGORY
  detailed_help = {'brief': 'Manage App Lifecycle Manager unit-operations.'}
