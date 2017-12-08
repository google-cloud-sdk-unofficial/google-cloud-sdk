# Copyright 2016 Google Inc. All Rights Reserved.
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
"""ml models list command."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base
from googlecloudsdk.core import apis
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List existing Cloud ML models."""

  def Collection(self):
    return 'ml.models'

  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    client = apis.GetClientInstance('ml', 'v1alpha3')
    msgs = apis.GetMessagesModule('ml', 'v1alpha3')
    req = msgs.MlProjectsModelsListRequest(
        projectsId=properties.VALUES.core.project.Get())
    return list_pager.YieldFromList(
        client.projects_models,
        req,
        field='models',
        batch_size_attribute='pageSize')
