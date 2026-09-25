# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2026 Google Inc. All Rights Reserved.
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
"""Command to delete an Apigee API proxy."""

from typing import Any

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class Delete(base.DeleteCommand):
  """Delete an Apigee API proxy."""

  detailed_help = {
      "DESCRIPTION": (
          """\
  {description}

  `{command}` deletes an API proxy and all of its revisions.

  The API proxy must not have any deployed revisions. To undeploy a revision,
  run `{parent_command} undeploy`. Deleting an API proxy cannot be undone."""
      ),
      "EXAMPLES": (
          """\
  To delete an API proxy called ``my-proxy'' given that its matching Cloud
  Platform project has been set in gcloud settings, run:

      $ {command} my-proxy

  To delete an API proxy called ``my-proxy'' in an organization called
  ``my-org'', run:

      $ {command} my-proxy --organization=my-org

  To delete an API proxy called ``my-proxy'' without prompting for
  confirmation, run:

      $ {command} my-proxy --quiet

  To delete an API proxy called ``my-proxy'' and print the deleted proxy as a
  JSON object, run:

      $ {command} my-proxy --format=json
  """
      ),
  }

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.api",
        "API proxy to be deleted. To get a list of available API proxies, run "
        "`{parent_command} list`.",
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()],
    )

  def Run(self, args: parser_extensions.Namespace) -> dict[str, Any]:
    """Run the delete command."""
    identifiers = args.CONCEPTS.api.Parse().AsDict()
    api_id = identifiers["apisId"]
    console_io.PromptContinue(
        message=(
            "API proxy [{}] and all of its revisions will be deleted.".format(
                api_id
            )
        ),
        cancel_on_no=True,
        cancel_string="Deletion aborted by user.",
    )
    result = apigee.APIsClient.Delete(identifiers)
    log.DeletedResource(api_id, kind="API proxy")
    return result
