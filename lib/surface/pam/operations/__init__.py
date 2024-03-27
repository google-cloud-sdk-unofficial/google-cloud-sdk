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


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Operations(base.Group):
  """Manage PAM Operations.

     The gcloud pam operations command group lets you manage Privileged
     Access Manager (PAM) Operations.

     ## EXAMPLES

     To display the details of an operation with the name operation-name,
     run:

     $ {command} describe operation-name

     To list all operations under project `sample-project` and location
     `global`, run:

     $ {command} --location=global --project=sample-project

     To list all operations under folder `sample-folder` and location
     `global`, run:

     $ {command} --location=global --folder=sample-folder

     To list all operations under organization `sample-organization` and
     location `global`, run:

     $ {command} --location=global --organization=sample-organization

     To delete an operation with the name operation-name, run:

     $ {command} delete operation-name

  """
