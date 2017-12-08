# Copyright 2015 Google Inc. All Rights Reserved.
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

"""The main command group for cloud dataproc."""

import argparse

from googlecloudsdk.calliope import base
from googlecloudsdk.core import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core import resolvers
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Dataproc(base.Group):
  """Create and manage Google Cloud Dataproc clusters and jobs."""

  # The only dataproc region
  REGION = 'global'

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To see how to create and manage clusters, run:

            $ {command} clusters

          To see how to submit and manage jobs, run:

            $ {command} jobs
          """,
  }

  def Filter(self, context, args):
    context['dataproc_messages'] = apis.GetMessagesModule('dataproc', 'v1')
    context['resources'] = resources

    # TODO(user): Move outside of context in a place that will be easier to
    # convert into a property when there are multiple regions.
    context['dataproc_region'] = self.REGION

    context['dataproc_client'] = apis.GetClientInstance('dataproc', 'v1')

    resources.SetParamDefault(
        api='dataproc',
        collection=None,
        param='projectId',
        resolver=resolvers.FromProperty(properties.VALUES.core.project))

    resources.SetParamDefault(
        api='dataproc',
        collection=None,
        param='region',
        resolver=lambda: context['dataproc_region'])

    return context
