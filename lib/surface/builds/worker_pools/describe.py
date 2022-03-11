# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Describe worker pool command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.build import utils
from googlecloudsdk.command_lib.container.fleet.features import base as hubbase
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(hubbase.DescribeCommand):
  """Describe a worker pool used by Google Cloud Build."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To get information about a worker pool named `wp1` in region `us-central1`, run:

            $ {command} wp1 --region=us-central1
          """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        '--region',
        required=True,
        help='The Cloud region where the worker pool is.')
    parser.add_argument(
        'WORKER_POOL', help='The ID of the worker pool to describe.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """

    wp_region = args.region

    release_track = self.ReleaseTrack()
    client = cloudbuild_util.GetClientInstance(release_track)
    messages = cloudbuild_util.GetMessagesModule(release_track)

    parent = properties.VALUES.core.project.Get(required=True)

    wp_name = args.WORKER_POOL

    # Get the workerpool ref
    wp_resource = resources.REGISTRY.Parse(
        None,
        collection='cloudbuild.projects.locations.workerPools',
        api_version=cloudbuild_util.RELEASE_TRACK_TO_API_VERSION[release_track],
        params={
            'projectsId': parent,
            'locationsId': wp_region,
            'workerPoolsId': wp_name,
        })

    # Send the Get request
    wp = client.projects_locations_workerPools.Get(
        messages.CloudbuildProjectsLocationsWorkerPoolsGetRequest(
            name=wp_resource.RelativeName()))

    if release_track != base.ReleaseTrack.ALPHA:
      if wp.hybridPoolConfig is not None:
        raise exceptions.Error('NOT_FOUND: Requested entity was not found.')

    # Format the workerpool name for display
    try:
      wp.name = cloudbuild_util.WorkerPoolShortName(wp.name)
    except ValueError:
      pass  # Must be an old version.

    return wp


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(Describe):
  """Describe a worker pool used by Google Cloud Build."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(Describe):
  """Describe a private or hybrid worker pool used by Google Cloud Build."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
            To get information about a private or hybrid worker pool named `wp1` in region `us-central1`, run:

              $ {command} wp1 --region=us-central1
            """,
  }

  feature_name = 'cloudbuild'

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        '--region',
        required=True,
        help='The Cloud region where the worker pool is.')
    parser.add_argument(
        'WORKER_POOL', help='The ID of the worker pool to describe.')
    parser.display_info.AddFormat("""
      multi(wp_status:format='table[box](
          NAME:label=NAME:sort=1,
          TYPE:label="TYPE",
          HWP_DESCRIPTION:label="CLUSTER DESCRIPTION":optional,
          HWP_STATUS:label=STATUS:optional
      )',
          wp_config:format=default)
    """)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """

    wp = super(DescribeAlpha, self).Run(args)

    wp_status = {
        'NAME': wp.name,
    }
    wp_out = {
        'wp_config': wp,
        'wp_status': wp_status
    }

    if wp.privatePoolV1Config is not None:
      wp_status[
          'TYPE'] = cloudbuild_util.WorkerpoolTypes.PRIVATE.name.capitalize()
    elif wp.hybridPoolConfig is not None:
      feature = self.GetFeature(v1alpha1=True)
      feature_state_memberships = utils.GetFeatureStateMemberships(feature)
      details = feature_state_memberships[wp.hybridPoolConfig.membership]
      wp_status.update({
          'TYPE': cloudbuild_util.WorkerpoolTypes.HYBRID.name.capitalize(),
          'HWP_DESCRIPTION': details.description,
          'HWP_STATUS': details.code,
      })
    else:
      wp_status[
          'TYPE'] = cloudbuild_util.WorkerpoolTypes.UNKNOWN.name.capitalize()

    return wp_out
