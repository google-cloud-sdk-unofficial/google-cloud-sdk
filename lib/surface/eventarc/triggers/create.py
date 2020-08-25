# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to create a trigger."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import triggers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import flags

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To create a new trigger 'my-trigger' for events of type 'google.cloud.pubsub.topic.v1.messagePublished' with destination Cloud Run service 'my-service', run:

          $ {command} my-trigger --matching-criteria="type=google.cloud.pubsub.topic.v1.messagePublished" --destination-run-service=my-service
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Create an Eventarc trigger."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddTriggerResourceArg(parser, 'The trigger to create.', required=True)
    flags.AddMatchingCriteriaArg(parser, required=True)
    flags.AddServiceAccountResourceArg(parser)
    flags.AddDestinationRunServiceResourceArg(parser, required=True)
    flags.AddDestinationRunPathArg(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run the create command."""
    client = triggers.TriggersClient()
    trigger_ref = args.CONCEPTS.trigger.Parse()
    service_account_ref = args.CONCEPTS.service_account.Parse()
    destination_run_service_ref = args.CONCEPTS.destination_run_service.Parse()
    operation = client.Create(trigger_ref, args.matching_criteria,
                              service_account_ref, destination_run_service_ref,
                              args.destination_run_path)
    if args.async_:
      return operation
    return client.WaitFor(operation)
