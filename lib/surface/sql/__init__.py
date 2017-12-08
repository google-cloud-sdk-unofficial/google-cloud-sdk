# Copyright 2013 Google Inc. All Rights Reserved.
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

"""The super-group for the sql CLI.

The fact that this is a directory with
an __init__.py in it makes it a command group. The methods written below will
all be called by calliope (though they are all optional).
"""
import argparse
import os
import re

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import apis
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core import resolvers
from googlecloudsdk.core import resources as cloud_resources
from googlecloudsdk.core.credentials import store as c_store

_ACTIVE_VERSIONS = [
    'v1beta3',
    'v1beta4',
]


def _Args(parser):
  parser.add_argument(
      '--api-version',
      help=argparse.SUPPRESS,
      choices=_ACTIVE_VERSIONS,
      action=actions.StoreProperty(
          properties.VALUES.api_endpoint_overrides.sql))


def _DoFilter(context, api_version_default):
  """Set up and return the context to be used by all SQL release tracks."""
  cloud_resources.SetParamDefault(
      api='sql', collection=None, param='project',
      resolver=resolvers.FromProperty(properties.VALUES.core.project))

  context['sql_client'] = apis.GetClientInstance('sql', api_version_default)
  context['sql_messages'] = apis.GetMessagesModule('sql', api_version_default)
  context['registry'] = cloud_resources.REGISTRY.CloneAndSwitchAPIs(
      context['sql_client'])

  return context


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SQL(base.Group):
  """Manage Cloud SQL databases."""

  @staticmethod
  def Args(parser):
    _Args(parser)

  @exceptions.RaiseToolExceptionInsteadOf(c_store.Error)
  def Filter(self, context, args):
    _DoFilter(context, 'v1beta3')


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SQLBeta(base.Group):
  """Manage Cloud SQL databases."""

  @staticmethod
  def Args(parser):
    _Args(parser)

  @exceptions.RaiseToolExceptionInsteadOf(c_store.Error)
  def Filter(self, context, args):
    _DoFilter(context, 'v1beta4')
