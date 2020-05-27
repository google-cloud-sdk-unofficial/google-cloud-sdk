# Copyright 2020 Google Inc. All Rights Reserved.  #
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
"""Command to list all deployments of an Apigee proxy."""
from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


class List(base.ListCommand):
  """List Apigee API proxy deployments."""

  detailed_help = {
      "DESCRIPTION": """\
  List Apigee proxy deployments.

  {command} lists all deployments that include a specific Apigee API proxy.
  """,
      "EXAMPLES": """\
  To list all deployments of an API proxy called ``my-proxy'' in the active
  Cloud Platform project, run:

      $ {command} --api=my-proxy

  To list all deployments of revision 4 of ``my-proxy'' in the active Cloud
  Platform project, run:

      $ {command} --revision=4 --api=my-proxy

  To list all deployments of ``my-proxy'' to the ``test'' environment in an
  Apigee organization called ``my-org'', run:

      $ {command} --organization=my-org --api=my-proxy --environment=test
  """}

  @staticmethod
  def Args(parser):
    help_text = {
        "api": "The API proxy whose deployments should be listed.",
        "environment": "The environment whose deployments should be listed. "
                       "If not provided, all environments will be listed.",
        "organization": "The organization whose deployments should be listed."
    }

    # `api` is a required argument for this command, but `environment` and
    # `revision` are not. In order to make `api` required, the whole resource
    # argument has to be "required" from gcloud concepts's point of view.
    #
    # Thus, to make `environment` and `revision` optional for the user, they
    # must be given fallthrough logic that fills in a placeholder value; this
    # value can then be recognized after parsing and interpreted as "no value
    # provided".
    #
    # Unfortunately, `None` won't work as the placeholder, because a fallthrough
    # class returning "None" means it was unable to provide a value at all.
    # Thus, some other value must be chosen.
    fallthroughs = [
        defaults.GCPProductOrganizationFallthrough(),
        # For `environment`, the placeholder must not be a string; any string
        # provided here might collide with a real environment name. Use the
        # Python builtin function all() as a convenient, idiomatic alternative.
        defaults.StaticFallthrough("environment", all),
        # For `revision`, the placeholder MUST be a string, because gcloud
        # concepts will try to parse it as a URL or fully qualified path, and
        # will choke on non-string values. This should be safe as all legitimate
        # revisions are numeric.
        defaults.StaticFallthrough("revision", "all")
    ]
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.environment.api.revision",
        "The API proxy revision whose deployments should be listed. If a "
        "`--revision` is not provided, all revisions will be listed.",
        positional=False,
        required=True,
        fallthroughs=fallthroughs,
        help_texts=help_text)
    parser.display_info.AddFormat("list")

  def Run(self, args):
    """Run the list command."""
    identifiers = args.CONCEPTS.revision.Parse().AsDict()
    if identifiers["environmentsId"] == all:
      del identifiers["environmentsId"]
    if identifiers["revisionsId"] == "all":
      del identifiers["revisionsId"]

    return apigee.DeploymentsClient.List(identifiers)
