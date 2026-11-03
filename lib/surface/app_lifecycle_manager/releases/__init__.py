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
"""The releases command group for the App Lifecycle Manager CLI."""

from googlecloudsdk.calliope import base


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Saas(base.Group):
  category = base.SAAS_CATEGORY
  detailed_help = {
      'brief': 'Manage App Lifecycle Manager releases.',
      'DESCRIPTION': """
          Manage App Lifecycle Manager releases. A release is a new version to
          be propagated and deployed to units. It includes a pointer to a
          blueprint, which is an Open Container Initiative (OCI) image stored
          in Artifact Registry or another OCI registry.
      """,
      'EXAMPLES': """
          To create a release named `my-release` for the unit kind
          `my-unit-kind` in location `us-central1`, run:

            $ {command} create my-release --location=us-central1 --unit-kind=my-unit-kind --blueprint-package=us-central1-docker.pkg.dev/my-project/my-repo/my-blueprint:v2

          To list the names of all releases in location `us-central1`, run:

            $ {command} list --location=us-central1 --format="value(name)"

          To describe the release named `my-release` in location `us-central1`,
          run:

            $ {command} describe my-release --location=us-central1
      """,
  }


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SaasAlpha(base.Group):
  category = base.SAAS_CATEGORY
  detailed_help = {'brief': 'Manage App Lifecycle Manager releases.'}
