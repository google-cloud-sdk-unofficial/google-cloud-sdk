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

"""The command group for the PAM Operations CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.UniverseCompatible
class Operations(base.Group):
  r"""Manage Privileged Access Manager (PAM) Long Running Operations.

  The `gcloud pam operations` command group lets you manage Privileged
  Access Manager (PAM) operations.

  ## EXAMPLES

  To describe an operation with the full name ``OPERATION_NAME'', run:

      $ {command} describe OPERATION_NAME

  To list all operations in a project named `sample-project` and in location
  `global`, run:

      $ {command} list --project=sample-project --location=global

  To list all operations in a folder with ID ``FOLDER_ID'' and in location
  `global`, run:

      $ {command} list --folder=FOLDER_ID --location=global

  To list all operations in an organization with ID ``ORGANIZATION_ID'' and in
  location `global`, run:

      $ {command} list --organization=ORGANIZATION_ID --location=global

  To delete an operation with the full name ``OPERATION_NAME'', run:

      $ {command} delete OPERATION_NAME

  To poll an operation with the full name ``OPERATION_NAME'', run:

      $ {command} wait OPERATION_NAME

  """
