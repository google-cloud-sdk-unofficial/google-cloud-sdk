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
"""Export environment command."""

import sys

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.util import files


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Export(base.Command):
  """Export a Managed Service for Apache Spark environment.

  Exporting an environment is similar to describing it, except that export
  omits the resource name, the etag, and output-only fields such as the
  revision ID. This allows the output of export to be passed directly to
  import.
  """

  detailed_help = {
      'EXAMPLES': """\
          To export environment `my-env` in `us-central1` to a file named
          `my-env.yaml`, run:

            $ {command} my-env --location=us-central1 --destination=my-env.yaml
          """,
  }

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack(), api_version='v2')
    flags.AddEnvironmentResourceArg(parser, 'export', dataproc.api_version)
    export_util.AddExportFlags(parser)

  def Run(self, args):
    environment_ref = args.CONCEPTS.environment.Parse()
    dataproc = dp.Dataproc(
        self.ReleaseTrack(),
        api_version='v2',
        location=environment_ref.locationsId,
    )
    request = dataproc.messages.DataprocProjectsLocationsEnvironmentsGetRequest(
        name=environment_ref.RelativeName()
    )
    environment = dataproc.client.projects_locations_environments.Get(request)

    # Filter out output-only fields and fields that identify this environment,
    # so that the output can be imported into any environment. The etag is
    # removed because it only matches the current contents of this
    # environment. Keep this list in sync with the v2 Environment message.
    environment.name = None
    environment.etag = None
    environment.createTime = None
    environment.revisionId = None
    environment.state = None
    environment.status = None
    environment.uid = None
    environment.updateTime = None

    if args.destination:
      with files.FileWriter(args.destination) as stream:
        export_util.Export(message=environment, stream=stream)
    else:
      export_util.Export(message=environment, stream=sys.stdout)
