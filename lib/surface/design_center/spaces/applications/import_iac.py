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
"""Command to import IaC for an Application."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.design_center import applications as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.design_center import flags
from googlecloudsdk.api_lib.design_center import utils

_DETAILED_HELP = {
    'DESCRIPTION': 'Import Infrastructure as Code (IaC) for a Design Center Application.',
    'EXAMPLES': """ \
        To import IaC from a Google Cloud Storage URI into the application `my-app` in space `dev-space` and location `us-central1`, run:

          $ {command} my-app --location=us-central1 --space=dev-space --gcs-uri=gs://my-bucket/iac

        To import IaC from a local YAML file named `iac_module.yaml` into the application `my-app` in space `dev-space` and location `us-central1`, run:

          $ {command} my-app --location=us-central1 --space=dev-space --iac-module-from-file=iac_module.yaml

        To import IaC from a Google Cloud Storage URI into the application `my-app`, allowing partial imports of valid edits, run:

          $ {command} my-app --location=us-central1 --space=dev-space --gcs-uri=gs://my-bucket/iac --allow-partial-import

        To import IaC from a local YAML file into the application `my-app`, allowing partial imports of valid edits, run:

          $ {command} my-app --location=us-central1 --space=dev-space --iac-module-from-file=iac_module.yaml --allow-partial-import

        To validate IaC from a Google Cloud Storage URI for the application `my-app` without importing, run:

          $ {command} my-app --location=us-central1 --space=dev-space --gcs-uri=gs://my-bucket/iac --validate-iac

        To validate IaC from a local YAML file for the application `my-app` without importing, run:

          $ {command} my-app --location=us-central1 --space=dev-space --iac-module-from-file=iac_module.yaml --validate-iac

        To validate IaC from a Google Cloud Storage URI for the application `my-app` and indicate that a future import should allow partial success, run:

          $ {command} my-app --location=us-central1 --space=dev-space --gcs-uri=gs://my-bucket/iac --validate-iac --allow-partial-import

        To validate IaC from a local YAML file for the application `my-app` and indicate that a future import should allow partial success, run:

          $ {command} my-app --location=us-central1 --space=dev-space --iac-module-from-file=iac_module.yaml --validate-iac --allow-partial-import
        """,
    'API REFERENCE': """ \
        This command uses the designcenter/v1alpha API. The full documentation for
        this API can be found at:
        http://cloud.google.com/application-design-center/docs
        """,
}



@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class ImportIac(base.Command):
  """Import Infrastructure as Code (IaC) for an Application."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddApplicationResourceArg(parser, verb='to import IaC into')
    flags.AddImportIacFlags(parser)

  def Run(self, args):
    client = apis.ApplicationsClient(self.ReleaseTrack())
    app_ref = args.CONCEPTS.application.Parse()

    iac_module_msg = None
    if args.iac_module_from_file:
      iac_module_data = flags.ParseIacModuleFile(args.iac_module_from_file)
      try:
        iac_module_msg = utils.ParseIaCModuleData(client, iac_module_data)
      except ValueError as e:
        raise flags.arg_parsers.ArgumentTypeError(
            'Invalid format for --iac-module-from-file: {}'.format(e))

    response = client.ImportIac(
        name=app_ref.RelativeName(),
        gcs_uri=args.gcs_uri,
        iac_module=iac_module_msg,
        allow_partial_import=args.allow_partial_import,
        validate_iac=args.validate_iac)
    return response


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.UniverseCompatible
class ImportIacGa(base.Command):
  """Import Infrastructure as Code (IaC) for an Application."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddApplicationResourceArg(parser, verb='to import IaC into')
    flags.AddImportIacFlags(parser)

  def Run(self, args):
    client = apis.ApplicationsClient(self.ReleaseTrack())
    app_ref = args.CONCEPTS.application.Parse()

    iac_module_msg = None
    if args.iac_module_from_file:
      iac_module_data = flags.ParseIacModuleFile(args.iac_module_from_file)
      try:
        iac_module_msg = utils.ParseIaCModuleData(client, iac_module_data)
      except ValueError as e:
        raise flags.arg_parsers.ArgumentTypeError(
            'Invalid format for --iac-module-from-file: {}'.format(e))

    response = client.ImportIac(
        name=app_ref.RelativeName(),
        gcs_uri=args.gcs_uri,
        iac_module=iac_module_msg,
        allow_partial_import=args.allow_partial_import,
        validate_iac=args.validate_iac)
    return response
