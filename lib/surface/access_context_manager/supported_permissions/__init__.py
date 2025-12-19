# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""The command group for the Access Context Manager supported-permissions CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SupportedPermissions(base.Group):
  """Retrieve VPC Service Controls Supported Permissions.

  The {command} command group lets you list VPC Service Controls supported
  permissions. It also lets you describe which permissions in a provided role
  are supported by VPC Service Controls.

  ## EXAMPLES

  To see all VPC Service Controls supported permissions:

    $ {command} list

  To see which permissions in a provided role are supported by VPC Service
    Controls:

    $ {command} describe roles/example.role.name
  """
