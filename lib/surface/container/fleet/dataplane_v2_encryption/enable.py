# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""The command to enable Multi-cluster Services Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.api_lib.util import exceptions as core_api_exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import retry


class Enable(base.EnableCommand):
  """Enables the Dataplane V2 Encryption Feature.

  This command enables the Dataplane V2 Encryption Feature in a fleet.

  ## EXAMPLES

  To enable the Dataplane V2 Encryption Feature, run:

    $ {command}
  """

  feature_name = 'dataplanev2'

  def Run(self, args):
    """Runs the command. No args."""
    feature = self.v1alpha1_messages.Feature(
        dataplanev2FeatureSpec=self.v1alpha1_messages.DataplaneV2FeatureSpec(
            enableEncryption=True
        )
    )
    project = properties.VALUES.core.project.GetOrFail()
    parent = util.LocationResourceName(project)
    req = self.v1alpha1_messages.GkehubProjectsLocationsGlobalFeaturesCreateRequest(
        feature=feature,
        featureId=self.feature_name,
        parent=parent,
    )
    retryer = retry.Retryer(max_retrials=4, exponential_sleep_multiplier=1.75)
    try:
      op = retryer.RetryOnException(
          self.v1alpha1_client.projects_locations_global_features.Create,
          args=(req,),
          should_retry_if=self._FeatureAPINotEnabled,
          sleep_ms=1000,
      )
    except retry.MaxRetrialsException:
      raise exceptions.Error(
          'Retry limit exceeded waiting for {} to enable'.format(
              self.feature.display_name
          )
      )
    except apitools_exceptions.HttpConflictError as e:
      # If the error is not due to the object already existing, re-raise.
      error = core_api_exceptions.HttpErrorPayload(e)
      if error.status_description != 'ALREADY_EXISTS':
        raise
      # TODO(b/177098463): Decide if this should be a hard error if a spec was
      # set, but not applied, because the Feature already existed.
      log.status.Print(
          '{} Feature for project [{}] is already enabled'.format(
              self.feature.display_name, project
          )
      )
      return
    msg = 'Waiting for Feature {} to be created'.format(
        self.feature.display_name
    )

    return self.WaitForHubOp(
        waiter.CloudOperationPoller(
            self.v1alpha1_client.projects_locations_global_features,
            self.v1alpha1_client.projects_locations_operations,
        ),
        op=op,
        message=msg,
    )
