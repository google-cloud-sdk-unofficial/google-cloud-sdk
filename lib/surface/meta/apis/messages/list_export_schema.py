# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""A command that lists a YAML export schema for a message from a given API."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.meta.apis import flags
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import export
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.core import log


class ListExportSchema(base.DescribeCommand):
  """List a YAML export schema for a message in a given API.

  *gcloud* commands that have "too many" *create*/*update* command flags may
  also provide *export*/*import* commands. *export* lists the current state
  of a resource in a YAML *export* format. *import* reads export format data
  and either creates a new resource or updates an existing resource.

  An export format is an abstract YAML representation of the mutable fields of a
  populated protobuf message. Abstraction allows the export format to hide
  implementation details of some protobuf constructs like enums and
  `additionalProperties`.

  One way of describing an export format is with a JSON schema. A schema
  documents export format properties and can also be used to validate data on
  import. Validation is important because users can modify export data before
  importing it again.

  This command lists a [JSON schema](json-schema.org) (in YAML format, go
  figure) for a protobuf message in an API.

  ## CAVEATS

  The generated schemas depend on the quality of the protobuf discovery
  docs, including proto file comment conventions that are not error checked.
  Always manually inspect schemas before using them in a release.

  ## EXAMPLES

  To generate the WorkflowTemplate schema in the dataproc v1beta2 API:

    $ {command} WorkflowTemplate --api=dataproc --api-version=v1beta2
  """

  @staticmethod
  def Args(parser):
    flags.API_REQUIRED_FLAG.AddToParser(parser)
    flags.API_VERSION_FLAG.AddToParser(parser)
    parser.add_argument(
        'message',
        help='The name of the message to list the YAML export schema for.')

  def Run(self, args):
    api = registry.GetAPI(args.api, api_version=args.api_version)
    try:
      message = getattr(api.GetMessagesModule(), args.message)
    except AttributeError:
      raise exceptions.InvalidArgumentException(
          'message', 'Message [{}] does not exist for API [{} {}]'.format(
              args.message, args.api, api.version))
    message_spec = arg_utils.GetRecursiveMessageSpec(message)
    text = export.GetExportSchema(api, args.message, message_spec)
    log.out.write(text)
