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
"""The saas command group for the App Lifecycle Manager CLI."""

from googlecloudsdk.calliope import base


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Saas(base.Group):
  category = base.SAAS_CATEGORY
  detailed_help = {
      'brief': 'Manage App Lifecycle Manager SaaS offerings.',
      'DESCRIPTION': """
          Manage App Lifecycle Manager SaaS offerings. A SaaS offering (also
          called an app offering) represents a SaaS product managed by the
          service producer. It defines the locations in which the product is
          available.
      """,
      'EXAMPLES': """
          To create a SaaS offering named `my-saas` in location `us-central1`
          that is available in `us-central1`, run:

            $ {command} create my-saas --location=us-central1 --locations=name=us-central1

          To list the names of all SaaS offerings in location `us-central1`,
          run:

            $ {command} list --location=us-central1 --format="value(name)"

          To describe the SaaS offering named `my-saas` in location
          `us-central1`, run:

            $ {command} describe my-saas --location=us-central1
      """,
  }


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SaasAlpha(base.Group):
  category = base.SAAS_CATEGORY
  detailed_help = {'brief': 'Manage App Lifecycle Manager saas.'}
