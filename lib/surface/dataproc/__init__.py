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

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resolvers
from googlecloudsdk.core import resources


DETAILED_HELP = {
    'DESCRIPTION': """\
        The gcloud dataproc command group lets you create and manage Google
        Cloud Dataproc clusters and jobs.

        Cloud Dataproc is an Apache Hadoop, Apache Spark, Apache Pig, and Apache
        Hive service. It easily processes big datasets at low cost, creating
        managed clusters of any size that scale down once processing is
        complete.

        More information on Cloud Dataproc can be found here:
        https://cloud.google.com/dataproc and detailed documentation can be
        found here: https://cloud.google.com/dataproc/docs/

        ## EXAMPLES

        To see how to create and manage clusters, run:

            $ {command} clusters

        To see how to submit and manage jobs, run:

            $ {command} jobs
        """,
}


# The default Dataproc region.
_DEFAULT_REGION = 'global'


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Dataproc(base.Group):
  """Create and manage Google Cloud Dataproc clusters and jobs."""
  detailed_help = DETAILED_HELP

  def Filter(self, context, args):
    context['dataproc_messages'] = apis.GetMessagesModule('dataproc', 'v1')
    context['resources'] = resources.REGISTRY

    # TODO(b/35708327): Move outside of context in a place that will be easier
    # to convert into a property when there are multiple regions.
    if hasattr(args, 'region'):
      context['dataproc_region'] = args.region
    else:
      context['dataproc_region'] = _DEFAULT_REGION

    context['dataproc_client'] = apis.GetClientInstance('dataproc', 'v1')

    resources.REGISTRY.SetParamDefault(
        api='dataproc',
        collection=None,
        param='projectId',
        resolver=resolvers.FromProperty(properties.VALUES.core.project))
    resources.REGISTRY.SetParamDefault(
        api='dataproc',
        collection=None,
        param='region',
        resolver=lambda: context['dataproc_region'])

    # These two properties are artifacts of how our Operations API get
    # converted into generated libraries.
    resources.REGISTRY.SetParamDefault(
        api='dataproc',
        collection=None,
        param='projectsId',
        resolver=resolvers.FromProperty(properties.VALUES.core.project))
    resources.REGISTRY.SetParamDefault(
        api='dataproc',
        collection=None,
        param='regionsId',
        resolver=lambda: context['dataproc_region'])

    return context


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DataprocBeta(Dataproc):
  """Create and manage Google Cloud Dataproc clusters and jobs."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--region',
        default=_DEFAULT_REGION,
        help=('Specifies the Dataproc region to use. Each Dataproc region '
              'constitutes an independent resource namespace constrained to '
              'deploying instances into GCE zones inside the region. The '
              'default value of "global" is a special multi-region namespace '
              'which is capable of deploying instances into all GCE zones '
              'globally, and is disjoint from other Dataproc regions. This '
              'region parameter corresponds to the /regions/<region> segment '
              'of the Dataproc resource URIs being referenced.'),
        hidden=True)

