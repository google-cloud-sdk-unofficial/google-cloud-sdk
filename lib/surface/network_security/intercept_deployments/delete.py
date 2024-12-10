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
"""Delete intercept deployment command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.api_lib.network_security.intercept_deployments import api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security.intercept import deployment_flags

DETAILED_HELP = {
    'DESCRIPTION': """
          Delete an intercept deployment. Check the progress of deployment deletion
          by using `gcloud network-security intercept-deployments list`.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To delete an intercept deployment called `my-deployment` in location `us-central1`, run:

            $ {command} my-deployment --location=us-central1-a --project=my-project

        """,
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Delete(base.DeleteCommand):
  """Delete an Intercept Deployment."""

  @classmethod
  def Args(cls, parser):
    deployment_flags.AddDeploymentResource(cls.ReleaseTrack(), parser)
    deployment_flags.AddMaxWait(
        parser, '20m'  # default to 20 minutes wait.
    )
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

  def Run(self, args):
    client = api.Client(self.ReleaseTrack())

    deployment = args.CONCEPTS.intercept_deployment.Parse()

    is_async = args.async_
    max_wait = datetime.timedelta(seconds=args.max_wait)

    operation = client.DeleteDeployment(name=deployment.RelativeName())

    # Return the in-progress operation if async is requested.
    if is_async:
      # Delete operations have their returned resource in YAML format by
      # default, but here we want the operation metadata to be printed.
      if not args.IsSpecified('format'):
        args.format = 'default'
      return operation
    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for intercept deployment [{}] to be deleted'.format(
            deployment.RelativeName()
        ),
        has_result=False,
        max_wait=max_wait,
    )


Delete.detailed_help = DETAILED_HELP
