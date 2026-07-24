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
"""Command for proxying to a given instance."""

import argparse
from googlecloudsdk.api_lib.run import container_resource
from googlecloudsdk.api_lib.run import instance
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.config import config_helper
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import messages_util
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import proxy
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.credentials import store


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Proxy(base.BinaryBackedCommand):
  """Proxy an instance to localhost authenticating as the active account or with the specified token.

  Runs a server on localhost that proxies requests to the specified Cloud Run
  Instance with credentials attached.

  You can use this to test instances protected with IAM authentication.

  The Cloud Run instance must be reachable from the machine running this
  command. For example, if the Cloud Run Instance is configured to only allow
  `internal` ingress, this command will not work from outside the instance's
  VPC network.
  """

  detailed_help = {
      'DESCRIPTION': (
          """\
          {description}
          """
      ),
      'EXAMPLES': (
          """\
          To proxy the instance 'my-instance' at localhost port 8080:

              $ {command} my-instance --port=8080
          """
      ),
  }

  @staticmethod
  def CommonArgs(parser: argparse.ArgumentParser) -> None:
    instance_presentation = presentation_specs.ResourcePresentationSpec(
        'INSTANCE',
        resource_args.GetInstanceResourceSpec(),
        'Instance to proxy locally.',
        required=True,
        prefixes=False,
    )
    flags.AddPortFlag(
        parser,
        help_text=(
            'Local port number to expose the proxied instance. '
            'If not specified, it will be set to 8080.'
        ),
    )
    flags.AddTokenFlag(parser)
    concept_parsers.ConceptParser([instance_presentation]).AddToParser(parser)

  @staticmethod
  def Args(parser: argparse.ArgumentParser) -> None:
    Proxy.CommonArgs(parser)

  def Run(self, args: argparse.Namespace) -> str | None:

    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )
    instance_ref = args.CONCEPTS.instance.Parse()
    flags.ValidateResource(instance_ref)
    with serverless_operations.Connect(conn_context) as client:
      instance_obj = client.GetInstance(instance_ref)
    if not instance_obj:
      raise exceptions.ArgumentError(
          messages_util.GetNotFoundMessage(
              conn_context, instance_ref, resource_kind='Instance'
          )
      )

    bind = '127.0.0.1:' + (args.port if args.port else '8080')
    host = self._GetUrl(instance_obj, instance_ref.instancesId)

    command_executor = proxy.ProxyWrapper()
    pretty_print.Info(
        messages_util.GetStartDeployMessage(
            conn_context,
            instance_ref,
            'Proxying to',
            resource_kind_lower='instance',
        )
    )
    pretty_print.Info('http://{} proxies to {}'.format(bind, host))

    if args.token:
      response = command_executor(host=host, token=args.token, bind=bind)
    else:
      # Keep restarting the proxy with fresh token before the token expires (1h)
      # until hitting a failure.
      while True:
        response = command_executor(
            host=host, token=_GetFreshIdToken(), bind=bind, duration='55m'
        )
        if response.failed:
          break

    return self._DefaultOperationResponseHandler(response)

  def _GetUrl(self, instance_obj: instance.Instance, instance_id: str) -> str:
    if (
        instance_obj.annotations.get(container_resource.DISABLE_URL_ANNOTATION)
        == 'true'
    ):
      raise exceptions.ArgumentError(
          'Instance [{}] has default URL disabled.'.format(instance_id)
      )
    if not instance_obj.urls:
      raise exceptions.ArgumentError(
          'URL for instance [{}] is not ready'.format(instance_id)
      )
    return instance_obj.urls[0]


def _GetFreshIdToken() -> str:
  cred = store.LoadFreshCredential()
  credential = config_helper.Credential(cred)
  return credential.id_token
