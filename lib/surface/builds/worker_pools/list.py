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
"""List worker pools command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List all worker pools in a Google Cloud project."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To fetch a list of worker pools running in region `us-central1`, run:

            $ {command} --region=us-central1
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
        help='The Cloud region to list worker pools in.')
    parser.display_info.AddFormat("""
          table(
            name,
            createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'),
            state
          )
        """)

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

    # Get the parent project ref
    parent_resource = resources.REGISTRY.Create(
        collection='cloudbuild.projects.locations',
        projectsId=parent,
        locationsId=wp_region)

    # Send the List request
    wp_list = client.projects_locations_workerPools.List(
        messages.CloudbuildProjectsLocationsWorkerPoolsListRequest(
            parent=parent_resource.RelativeName())).workerPools

    # Format the workerpool names for display
    for wp in wp_list:
      if release_track != base.ReleaseTrack.ALPHA:
        if wp.hybridPoolConfig is not None:
          wp_list.remove(wp)
      try:
        wp.name = cloudbuild_util.WorkerPoolShortName(wp.name)
      except ValueError:
        pass  # Must be an old version.

    return wp_list


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List all worker pools in a Google Cloud project."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(List):
  """List all private and hybrid worker pools in a Google Cloud project."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To fetch a list of all private and hybrid worker pools running in region `us-central1`, run:

            $ {command} --region=us-central1

          To fetch a list of only hybrid worker pools running in region `us-central1`, run:

            $ {command} --region=us-central1 --filter="type:Hybrid"
          """,
  }

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To fetch a list of all private and hybrid worker pools running in region `us-central1`, run:

            $ {command} --region=us-central1

          To fetch a list of only hybrid worker pools running in region `us-central1`, run:

            $ {command} --region=us-central1 --filter="type:Hybrid"
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
        help='The Cloud region to list worker pools in.')
    parser.display_info.AddFormat("""
            table[all-box](
            wp.name,
            type:label="TYPE",
            wp.createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'),
            wp.state
          )
        """)

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

    # Get the parent project ref
    parent_resource = resources.REGISTRY.Create(
        collection='cloudbuild.projects.locations',
        projectsId=parent,
        locationsId=wp_region)

    # Send the List request
    wp_list = client.projects_locations_workerPools.List(
        messages.CloudbuildProjectsLocationsWorkerPoolsListRequest(
            parent=parent_resource.RelativeName())).workerPools

    wp_out = []
    # Format the workerpool names for display and determine workerpool type
    for wp in wp_list:
      wp_type = cloudbuild_util.WorkerpoolTypes.UNKNOWN.name.capitalize()
      if wp.privatePoolV1Config is not None:
        wp_type = cloudbuild_util.WorkerpoolTypes.PRIVATE.name.capitalize()
      elif wp.hybridPoolConfig is not None:
        wp_type = cloudbuild_util.WorkerpoolTypes.HYBRID.name.capitalize()
      try:
        wp.name = cloudbuild_util.WorkerPoolShortName(wp.name)
      except ValueError:
        pass  # Must be an old version.
      wp_out.append({'wp': wp, 'type': wp_type})

    return wp_out
