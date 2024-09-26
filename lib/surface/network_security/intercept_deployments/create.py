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
"""Create intercept deployment command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.api_lib.network_security.intercept_deployments import api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security.intercept import deployment_flags
from googlecloudsdk.command_lib.util.args import labels_util

DETAILED_HELP = {
    'DESCRIPTION': """
          Create an intercept deployment. Successful creation of a deployment results
          in a deployment in ACTIVE state. Check the progress of deployment creation
          by using `gcloud network-security intercept-deployments list`.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To create an intercept deployment called `my-deployment`, in project ID `my-project` and zone `us-central1-a`, run:
            $ {command} my-deployment --project=my-project --location=us-central1-a --deployment-group-location=global
            --forwarding-rule=my-forwarding-rule --forwarding-rule-location=us-central1 --intercept-deployment-group=my-deployment-group

            OR

            $ {command} my-deployment --project=my-project --location=us-central1-a
            --forwarding-rule=projects/my-project/regions/us-central1/forwardingRules/my-forwarding-rule
            --intercept-deployment-group=projects/my-project/locations/global/interceptDeploymentGroups/my-deployment-group

            OR

            $ {command} projects/my-project/locations/us-central1/interceptDeployments/my-deployment
            --forwarding-rule=projects/my-project/regions/us-central1/forwardingRules/my-forwarding-rule
            --intercept-deployment-group=projects/my-project/locations/global/interceptDeploymentGroups/my-deployment-group

        """,
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create an Intercept Deployment."""

  @classmethod
  def Args(cls, parser):
    deployment_flags.AddDeploymentResource(cls.ReleaseTrack(), parser)
    deployment_flags.AddForwardingRuleResource(parser)
    deployment_flags.AddInterceptDeploymentGroupResource(
        cls.ReleaseTrack(), parser
    )
    deployment_flags.AddMaxWait(
        parser,
        '20m',  # default to 20 minutes wait.
    )
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    client = api.Client(self.ReleaseTrack())

    deployment = args.CONCEPTS.intercept_deployment.Parse()
    forwarding_rule = args.CONCEPTS.forwarding_rule.Parse()
    intercept_deployment_group = (
        args.CONCEPTS.intercept_deployment_group.Parse()
    )
    labels = labels_util.ParseCreateArgs(
        args, client.messages.InterceptDeployment.LabelsValue
    )

    is_async = args.async_
    max_wait = datetime.timedelta(seconds=args.max_wait)

    operation = client.CreateDeployment(
        deployment_id=deployment.Name(),
        parent=deployment.Parent().RelativeName(),
        forwarding_rule=forwarding_rule.RelativeName(),
        intercept_deployment_group=intercept_deployment_group.RelativeName(),
        labels=labels,
    )
    # Return the in-progress operation if async is requested.
    if is_async:
      # Create operations have their returned resource in YAML format by
      # default, but here we want the operation metadata to be printed.
      if not args.IsSpecified('format'):
        args.format = 'default'
      return operation
    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            'waiting for intercept deployment [{}] to be created'.format(
                deployment.RelativeName()
            )
        ),
        has_result=True,
        max_wait=max_wait,
    )


Create.detailed_help = DETAILED_HELP
