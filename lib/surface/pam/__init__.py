# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""The command group for the PAM CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Pam(base.Group):
  r"""Manage Privileged Access Manager (PAM) Entitlements and Grants.

  The gcloud pam command group lets you manage Privileged Access Manager
  (PAM) Entitlements and Grants.

  ## EXAMPLES

  To check the PAM onboarding status for a project `sample-project` and
  location `global`, run:

      $ {command} check-onboarding-status --project=sample-project
      --location=global

  To check the PAM onboarding status for a folder `sample-folder` and
  location `global`, run:

      $ {command} check-onboarding-status --folder=sample-folder
      --location=global

  To check the PAM onboarding status for an organization
  `sample-organization` and location `global`, run:

      $ {command} check-onboarding-status --organization=sample-organization
      --location=global

  """
