# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Describe a Dataflow ConfigStore setting."""

from googlecloudsdk.api_lib.dataflow import apis as dataflow_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import config_store_util


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe a Dataflow ConfigStore setting."""

  detailed_help = {
      'DESCRIPTION': 'Describe a Dataflow ConfigStore setting.',
      'EXAMPLES': (
          """\
          To describe a setting on a project (note: the project must be
          specified as a project number, not a project ID):

            $ {command} default_launcher_machine_type \\
              --project=123456789012 --location=us-central1

          To describe the same setting on a folder or an organization:

            $ {command} default_launcher_machine_type \\
              --folder=123456 --location=us-central1

            $ {command} default_launcher_machine_type \\
              --organization=789012 --location=us-central1
          """
      ),
  }

  @staticmethod
  def Args(parser):
    config_store_util.AddConfigStoreSettingResourceArg(parser, 'to describe')

  def Run(self, args):
    parsed_resource = args.CONCEPTS.setting.Parse()
    setting_ref = parsed_resource.result
    resource_type = parsed_resource.concept_type.name

    client = dataflow_apis.GetClientInstance()
    messages = dataflow_apis.GetMessagesModule()

    service_map = {
        'project_setting': (
            client.projects_locations_configStoreSettings,
            messages.DataflowProjectsLocationsConfigStoreSettingsGetRequest,
        ),
        'folder_setting': (
            client.folders_locations_configStoreSettings,
            messages.DataflowFoldersLocationsConfigStoreSettingsGetRequest,
        ),
        'org_setting': (
            client.organizations_locations_configStoreSettings,
            messages.DataflowOrganizationsLocationsConfigStoreSettingsGetRequest,
        ),
    }
    service, request_cls = service_map[resource_type]
    request = request_cls(name=setting_ref.RelativeName())
    return service.Get(request)
