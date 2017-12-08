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

"""The command group for the Autoscaler CLI."""

import argparse

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import apis as core_apis
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resolvers
from googlecloudsdk.core import resources
from googlecloudsdk.core.credentials import store


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Autoscaler(base.Group):
  """Manage autoscalers of cloud resources."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--zone', required=True, help='Autoscaler Zone name',
        action=actions.StoreProperty(properties.VALUES.compute.zone))

  @exceptions.RaiseToolExceptionInsteadOf(store.Error)
  def Filter(self, context, args):
    client = core_apis.GetClientInstance('autoscaler', 'v1beta2')
    context['autoscaler-client'] = client

    messages_v2 = core_apis.GetMessagesModule('autoscaler', 'v1beta2')
    context['autoscaler_messages_module'] = messages_v2

    resources.SetParamDefault(
        api='compute',
        collection=None,
        param='project',
        resolver=resolvers.FromProperty(properties.VALUES.core.project))
    resources.SetParamDefault(
        api='autoscaler',
        collection=None,
        param='project',
        resolver=resolvers.FromProperty(properties.VALUES.core.project))
    resources.SetParamDefault(
        api='autoscaler',
        collection=None,
        param='zone',
        resolver=resolvers.FromProperty(properties.VALUES.compute.zone))
    resources.SetParamDefault(
        api='replicapool',
        collection=None,
        param='project',
        resolver=resolvers.FromProperty(properties.VALUES.core.project))
    resources.SetParamDefault(
        api='replicapool',
        collection=None,
        param='zone',
        resolver=resolvers.FromProperty(properties.VALUES.compute.zone))

    context['autoscaler_resources'] = resources
    return context
