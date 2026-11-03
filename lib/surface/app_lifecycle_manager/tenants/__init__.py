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
"""The tenants command group for the App Lifecycle Manager CLI."""

from googlecloudsdk.calliope import base


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Saas(base.Group):
  category = base.SAAS_CATEGORY
  detailed_help = {
      'brief': 'Manage App Lifecycle Manager tenants.',
      'DESCRIPTION': """
          Manage App Lifecycle Manager tenants. A tenant represents the
          service producer side of an instance of the service that is created
          based on a request from a consumer. A tenant usually maps one-to-one
          to a resource given out to a service consumer.
      """,
      'EXAMPLES': """
          To create a tenant named `my-tenant` for the SaaS offering `my-saas`
          in location `us-central1`, run:

            $ {command} create my-tenant --location=us-central1 --saas=my-saas

          To list the names of all tenants in location `us-central1`, run:

            $ {command} list --location=us-central1 --format="value(name)"

          To describe the tenant named `my-tenant` in location `us-central1`,
          run:

            $ {command} describe my-tenant --location=us-central1
      """,
  }


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SaasAlpha(base.Group):
  category = base.SAAS_CATEGORY
  detailed_help = {'brief': 'Manage App Lifecycle Manager tenants.'}
