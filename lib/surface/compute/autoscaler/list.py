# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Command for listing autoscalers."""

from googlecloudsdk.api_lib.compute import autoscaler_utils as util
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import list_printer
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.third_party.apitools.base.py import exceptions
from googlecloudsdk.third_party.apitools.base.py import list_pager


class ListAutoscalers(base_classes.BaseCommand):
  """List Autoscaler instances."""

  # TODO(user): Add --limit flag.
  def Run(self, args):
    log.warn('Please use instead [gcloud compute instance-groups '
             'managed list].')
    client = self.context['autoscaler-client']
    messages = self.context['autoscaler_messages_module']
    resources = self.context['autoscaler_resources']
    try:
      request = messages.AutoscalerAutoscalersListRequest()
      request.project = properties.VALUES.core.project.Get(required=True)
      request.zone = resources.Parse(
          args.zone, collection='compute.zones').zone
      return list_pager.YieldFromList(client.autoscalers, request)

    except exceptions.HttpError as error:
      raise calliope_exceptions.HttpException(util.GetErrorMessage(error))
    except ValueError as error:
      raise calliope_exceptions.HttpException(error)

  def Display(self, unused_args, result):
    list_printer.PrintResourceList('autoscaler.instances', result)
