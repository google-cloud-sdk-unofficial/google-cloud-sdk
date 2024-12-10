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
"""Update deployment command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.network_security.intercept_deployments import api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.network_security.intercept import deployment_flags
from googlecloudsdk.command_lib.util.args import labels_util


DETAILED_HELP = {
    'DESCRIPTION': """
          Update an intercept deployment. Check the progress of deployment update
          by using `gcloud network-security intercept-deployments list`.

          For examples refer to the EXAMPLES section below.
        """,
    'EXAMPLES': """
            To update labels k1 and k2, run:

            $ {command} my-deployment --project=my-project --location=us-central1-a --update-labels=k1=v1,k2=v2

            To remove labels k3 and k4, run:

            $ {command} my-deployment --project=my-project --location=us-central1-a --remove-labels=k3,k4

            To clear all labels from the intercept deployment, run:

            $ {command} my-deploymen --project=my-project --location=us-central1-a --clear-labels
        """,
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Update(base.UpdateCommand):
  """Update an Intercept Deployment."""

  _valid_arguments = [
      '--clear-labels',
      '--remove-labels',
      '--update-labels',
  ]

  @classmethod
  def Args(cls, parser):
    deployment_flags.AddDeploymentResource(cls.ReleaseTrack(), parser)
    deployment_flags.AddMaxWait(
        parser,
        '20m',  # default to 20 minutes wait.
    )
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    client = api.Client(self.ReleaseTrack())

    deployment = args.CONCEPTS.intercept_deployment.Parse()
    try:
      original = client.DescribeDeployment(deployment.RelativeName())
    except apitools_exceptions.HttpNotFoundError:
      raise exceptions.InvalidArgumentException(
          'intercept-deployment',
          'Intercept deployment does not exist.',
      )

    update_fields = {}
    labels = self._process_label_updates(client, args, original)
    if labels:
      update_fields['labels'] = labels

    if not update_fields:
      raise exceptions.MinimumArgumentException(self._valid_arguments)

    operation = client.UpdateDeployment(
        name=deployment.RelativeName(),
        update_fields=update_fields,
    )

    # Returns the in-progress operation if async is requested.
    if args.async_:
      # Update operations have their returned resource in YAML format by
      # default, but here we want the operation metadata to be printed.
      if not args.IsSpecified('format'):
        args.format = 'default'
      return operation

    return self._wait_for_operation(
        client,
        operation,
        deployment,
        datetime.timedelta(seconds=args.max_wait),
    )

  def _process_label_updates(self, client, args, original_deployment):
    """Processes the label update request.

    Args:
      client: the client to use to make the API call.
      args: the args from the command line.
      original_deployment: the original intercept deployment.

    Returns:
      the labels we would like to update if there is any update. Otherwise,
      it returns None.
    """
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if not labels_diff.MayHaveUpdates():
      return None

    labels = original_deployment.labels
    labels_update = labels_diff.Apply(
        client.messages.InterceptDeployment.LabelsValue,
        labels,
    )
    if labels_update.needs_update:
      labels = labels_update.labels

    return labels

  def _wait_for_operation(self, client, operation, deployment, max_wait):
    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            'waiting for intercept deployment [{}] to be updated'.format(
                deployment.RelativeName()
            )
        ),
        has_result=False,
        max_wait=max_wait,
    )


Update.detailed_help = DETAILED_HELP
