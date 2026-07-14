# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Command to import an Apigee API proxy."""

import os

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args
from googlecloudsdk.command_lib.apigee.aft import compiler
from googlecloudsdk.command_lib.apigee.aft import converter
from googlecloudsdk.command_lib.apigee.aft import models
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Import(base.DescribeCommand):
  """Import an Apigee API proxy from local files."""

  detailed_help = {
      "DESCRIPTION": (
          """\
  {description}

  `{command}` uploads local files describing an API proxy to Apigee. If an API
  proxy with the given name already exists, a new revision is created;
  otherwise, a new API proxy is created.

  The API proxy source is provided in exactly one of two formats. Use
  `--from-bundle` to upload a standard Apigee API proxy bundle ZIP, which stores
  the proxy configuration under an `apiproxy/` directory. Use `--from-template`
  to build the API proxy from an Apigee Feature Template: a YAML file that
  composes one or more reusable feature files into an API proxy, which is
  compiled into a bundle locally before being uploaded.

  When using `--from-template`, any feature files referenced by the template
  must reside in the same directory as the template file.

  To use this command, the active Cloud Platform project must have an associated
  Apigee organization, or an organization must be specified with
  `--organization` or by providing the fully qualified name (FQN) of the API
  proxy as the API proxy name (for example,
  ``organizations/my-org/apis/helloworld'')."""
      ),
      "EXAMPLES": (
          """\
  To import an API proxy named ``helloworld'' from a local bundle ZIP, given
  that the matching Cloud Platform project has been set in gcloud settings, run:

    $ {command} helloworld --from-bundle=./helloworld.zip

  To import an API proxy named ``helloworld'' from an Apigee Feature Template,
  run:

    $ {command} helloworld --from-template=./helloworld.yaml

  To import that API proxy into an organization named ``my-org'', run:

    $ {command} helloworld --organization=my-org \\
        --from-template=./helloworld.yaml

  Alternatively, the organization can be specified by providing the fully
  qualified name of the API proxy:

    $ {command} organizations/my-org/apis/helloworld \\
        --from-bundle=./helloworld.zip

  To import that API proxy and print the resulting revision as a JSON object,
  run:

    $ {command} helloworld --from-template=./helloworld.yaml --format=json"""
      ),
  }

  @classmethod
  def Args(cls, parser):
    source_group = parser.add_mutually_exclusive_group(
        required=True,
        help="Source from which to import the API proxy.",
    )
    source_group.add_argument(
        "--from-template",
        dest="template_path",
        type=files.ExpandHomeDir,
        help=(
            "Path to an Apigee Feature Template YAML file to import the API "
            "proxy from.\n\n"
            "The template composes one or more reusable feature files into "
            "an API proxy. Any feature files referenced by the template must "
            "reside in the same directory as the template file. The template "
            "is compiled into an API proxy bundle locally before being "
            "uploaded to Apigee."
        ),
    )
    source_group.add_argument(
        "--from-bundle",
        dest="bundle_path",
        type=files.ExpandHomeDir,
        help=(
            "Path to an Apigee API proxy bundle ZIP file to import the API "
            "proxy from.\n\n"
            "The ZIP file must contain the API proxy configuration under "
            "an `apiproxy/` directory."
        ),
    )
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.api",
        "API proxy to import or update. If an API proxy with this name already "
        "exists in the organization, a new revision is created.",
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()],
    )

  def Run(self, args):
    """Run the import command."""
    identifiers = args.CONCEPTS.api.Parse().AsDict()

    bundle_path = args.bundle_path
    if args.template_path:
      template = models.from_dict(
          models.Template,
          yaml.load(files.ReadFileContents(args.template_path))
      )
      template_dir = os.path.dirname(args.template_path)
      referenced_feature_yaml = [
          files.ReadFileContents(os.path.join(template_dir, f))
          for f in template.features
      ]
      features = [
          models.from_dict(models.Feature, yaml.load(yaml_contents))
          for yaml_contents in referenced_feature_yaml
      ]
      compiled_proxy = compiler.ApigeeCompiler().compile(
          template, features, {}
      )
      bundle = converter.proxy_to_bundle(compiled_proxy)
      return apigee.APIsClient.Create(identifiers, {}, bundle)

    with files.BinaryFileReader(bundle_path) as f:
      return apigee.APIsClient.Create(identifiers, {}, f)
