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
"""The command group for cloud dataproc environments revisions."""

from googlecloudsdk.calliope import base


@base.DefaultUniverseOnly
@base.Hidden
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Revisions(base.Group):
  """Manage the revisions of a Managed Service for Apache Spark environment.

  Every create or update of an environment builds a new immutable revision. A
  build that fails is kept as a revision in state `FAILED`.

  ## EXAMPLES

  To list the revisions of an environment, run:

    $ {command} list --environment=my-env --location=us-central1

  To describe a revision, run:

    $ {command} describe my-rev --environment=my-env --location=us-central1

  To delete a revision, run:

    $ {command} delete my-rev --environment=my-env --location=us-central1
  """
