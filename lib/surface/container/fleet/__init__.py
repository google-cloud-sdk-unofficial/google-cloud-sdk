# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command group for Fleet."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Fleet(base.Group):
  """Centrally manage features and services on all your Kubernetes clusters with Fleet.

  The command group to register GKE or other Kubernetes clusters running in a
  variety of environments, including Google cloud, on premises in customer
  datacenters, or other third party clouds with Fleet. Fleet provides a
  centralized control-plane to managed features and services on all registered
  clusters.

  Each project can have only one fleet.

  ## EXAMPLES

  Manage a project's fleet:

    $ {command} --help
  """

  def Filter(self, context, args):
    """See base class."""
    base.RequireProjectID(args)
    return context
