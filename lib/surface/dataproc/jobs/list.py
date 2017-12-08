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

"""List job command."""

from apitools.base.py import encoding

from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties


STATE_MATCHER_ENUM = ['active', 'inactive']


class TypedJob(util.Bunch):
  """Job with additional type field that corresponds to the job_type one_of."""

  def __init__(self, job):
    super(TypedJob, self).__init__(encoding.MessageToDict(job))
    self._job = job
    self._type = None

  @property
  def type(self):
    for field in [field.name for field in self._job.all_fields()]:
      if field.endswith('Job'):
        job_type, _, _ = field.rpartition('Job')
        if self._job.get_assigned_value(field):
          return job_type
    raise AttributeError('Job has no job type')


class List(base.ListCommand):
  """List all jobs in a project."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To see the list of all jobs, run:

            $ {command}

          To see the list of all active jobs in a cluster, run:

            $ {command} --state-filter active --cluster my_cluster
          """,
  }

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)

    parser.add_argument(
        '--cluster',
        help='Restrict to the jobs of this Dataproc cluster.')

    parser.add_argument(
        '--state-filter',
        choices=STATE_MATCHER_ENUM,
        help='Filter by job state. Choices are {0}.'.format(STATE_MATCHER_ENUM))

  def Collection(self):
    return 'dataproc.jobs'

  @util.HandleHttpError
  def Run(self, args):
    client = self.context['dataproc_client']
    messages = self.context['dataproc_messages']

    project = properties.VALUES.core.project.Get(required=True)
    region = self.context['dataproc_region']
    request = messages.DataprocProjectsRegionsJobsListRequest(
        projectId=project, region=region)

    if args.cluster:
      request.clusterName = args.cluster

    if args.state_filter:
      if args.state_filter == 'active':
        request.jobStateMatcher = (
            messages.DataprocProjectsRegionsJobsListRequest
            .JobStateMatcherValueValuesEnum.ACTIVE)
      elif args.state_filter == 'inactive':
        request.jobStateMatcher = (
            messages.DataprocProjectsRegionsJobsListRequest
            .JobStateMatcherValueValuesEnum.NON_ACTIVE)
      else:
        raise exceptions.ToolException(
            'Invalid state-filter; [{0}].'.format(args.state_filter))

    response = client.projects_regions_jobs.List(request)
    return [TypedJob(job) for job in response.jobs]
