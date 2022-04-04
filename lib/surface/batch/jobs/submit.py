# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to submit a specified Batch job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.batch import jobs
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.batch import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


class Submit(base.Command):
  """Submit a Batch job.

  This command can fail for the following reasons:
  * The active account does not have permission to create the Batch job.

  ## EXAMPLES

  To submit the job with config.json sample config file and name
  `projects/foo/locations/us-central1/jobs/bar`, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar --config config.json
  """

  @staticmethod
  def Args(parser):
    resource_args.AddJobResourceArgs(parser)
    network_group = parser.add_group()
    network_group.add_argument(
        '--network',
        required=True,
        type=str,
        help="""The URL for the network resource.
        Must specify subnetwork as well if network is specified""")
    network_group.add_argument(
        '--subnetwork',
        required=True,
        type=str,
        help="""The URL for the subnetwork resource.
        Must specify network as well if subnetwork is specified""")

    parser.add_argument(
        '--config', required=True, help='The config file of a job.')

    parser.add_argument(
        '--priority',
        type=arg_parsers.BoundedInt(0, 99),
        help='Job priority [0-99] 0 is the lowest priority.')

    parser.add_argument(
        '--allowed-machine-types',
        metavar='MACHINE_TYPE',
        type=arg_parsers.ArgList(),
        help="""A list of allowed Compute Engine machine types, for
      example, e2-standard-4. Default is empty which means allowing all.""")

  def Run(self, args):
    job_ref = args.CONCEPTS.job.Parse()
    job_id = job_ref.RelativeName().split('/')[-1]
    location_ref = job_ref.Parent()

    batch_client = jobs.JobsClient()
    batch_msgs = jobs.GetMessagesModule()

    job_msg = self._CreateJobMessage(batch_msgs, args.config)

    if args.priority:
      job_msg.priority = args.priority

    if job_msg.allocationPolicy is None:
      job_msg.allocationPolicy = batch_msgs.AllocationPolicy()

    if args.allowed_machine_types:
      if job_msg.allocationPolicy.instance is None:
        job_msg.allocationPolicy.instance = batch_msgs.InstancePolicy(
            allowedMachineTypes=[])
      combined_allowed_machine_types = args.allowed_machine_types + job_msg.allocationPolicy.instance.allowedMachineTypes
      job_msg.allocationPolicy.instance.allowedMachineTypes = combined_allowed_machine_types

    if args.network and args.subnetwork:
      if job_msg.allocationPolicy.network is None:
        job_msg.allocationPolicy.network = batch_msgs.NetworkPolicy(
            networkInterfaces=[])
      job_msg.allocationPolicy.network.networkInterfaces.insert(
          0,
          batch_msgs.NetworkInterface(
              network=args.network, subnetwork=args.subnetwork))

    resp = batch_client.Create(job_id, location_ref, job_msg)
    log.status.Print(
        'Job {jobName} was successfully submitted.'.format(jobName=resp.uid))
    return resp

    # TODO(b/216858129): add HEREDOC support.
  def _CreateJobMessage(self, batch_msgs, config):
    """Construct the job proto with the config input."""
    file_contents = files.ReadFileContents(config)
    return encoding.JsonToMessage(batch_msgs.Job, file_contents)
