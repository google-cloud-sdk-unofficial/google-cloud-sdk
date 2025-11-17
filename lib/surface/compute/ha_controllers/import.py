# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""Command to import an HA Controller to a YAML file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.ha_controllers import utils as api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.ha_controllers import utils
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io


def _DetailedHelp():
  return {
      'brief':
          'Import an HA Controller.',
      'DESCRIPTION':
          """\
          Imports an High Availability (HA) Controller's configuration from a
          file.
          """,
      'EXAMPLES':
          """\
          An HA Controller can be imported by running:

            $ {command} my-ha-controller --source=<path-to-file>
          """
  }


def _GetApiVersion(release_track):
  """Returns the API version for the HA Controller."""
  if release_track == base.ReleaseTrack.ALPHA:
    return 'alpha'


def _GetSchemaPath(release_track, for_help=False):
  """Returns the schema path for the HA Controller."""
  return export_util.GetSchemaPath(
      'compute',
      _GetApiVersion(release_track),
      'HaController',
      for_help=for_help,
  )


def _CompareHaControllers(old_ha_controller, new_ha_controller):
  """Compares existing HA Controller with the imported one to see if a patch is needed."""
  for field_name, new_value in new_ha_controller.items():
    old_value = old_ha_controller.get(field_name)
    if new_value != old_value:
      return True
  return False


def _ReadResourceFromYaml(yaml_data, release_track):
  """Reads, validates and fixes structure of the YAML data."""
  data = console_io.ReadFromFileOrStdin(yaml_data, binary=False)
  yaml_data = yaml.load(data)
  export_util.ValidateYAML(
      yaml_data, _GetSchemaPath(release_track)
  )
  yaml_data = utils.FixImportStructure(yaml_data)
  return yaml_data


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Import(base.ImportCommand):
  """Import an HA Controller.

  Import an High Availability (HA) Controller, which helps
  ensure that a virtual machine (VM) instance remains operational by
  automatically managing failover across two zones.
  """

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    utils.AddHaControllerNameArgToParser(
        parser, base.ReleaseTrack.ALPHA.name.lower()
    )
    export_util.AddImportFlags(
        parser, _GetSchemaPath(base.ReleaseTrack.ALPHA, for_help=True))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    ha_controller_ref = args.CONCEPTS.ha_controller.Parse()

    # Import HA Controller from YAML file.
    yaml_data = _ReadResourceFromYaml(args.source or '-', self.ReleaseTrack())
    ha_controller = export_util.Import(
        message_type=client.messages.HaController,
        stream=yaml.dump(yaml_data),
    )
    ha_controller.name = ha_controller_ref.Name()
    ha_controller.region = ha_controller_ref.region

    # Try to get the existing HA Controller.
    try:
      old_ha_controller = api_utils.Get(client, ha_controller_ref)
      old_ha_controller = yaml.load(
          export_util.Export(
              message=old_ha_controller,
              schema_path=_GetSchemaPath(self.ReleaseTrack()),
          )
      )
    except apitools_exceptions.HttpError as error:
      if error.status_code != 404:
        raise error
      # HA Controller does not exist, create a new one.
      return api_utils.Insert(
          holder, ha_controller, ha_controller_ref, args.async_
      )

    has_diff = _CompareHaControllers(old_ha_controller, yaml_data)
    if not has_diff:
      # No change in the fields provided in the import file, do not send
      # requests to server.
      log.status.Print(
          'No changes detected in the HA Controller [{0}]. Skipping update.'
          .format(ha_controller_ref.Name())
      )
      return

    console_io.PromptContinue(
        message=('HA Controller [{0}] will be overwritten.').format(
            ha_controller_ref.Name()
        ),
        cancel_on_no=True,
    )

    return api_utils.Patch(
        holder, ha_controller, ha_controller_ref, args.async_
    )
