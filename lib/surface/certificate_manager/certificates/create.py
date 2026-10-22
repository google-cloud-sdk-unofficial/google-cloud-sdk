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
"""`gcloud certificate-manager certificates create` command."""

from googlecloudsdk.api_lib.certificate_manager import certificates
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.certificate_manager import flags
from googlecloudsdk.command_lib.certificate_manager import resource_args
from googlecloudsdk.command_lib.certificate_manager import util
from googlecloudsdk.command_lib.util.args import labels_util


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Create(base.CreateCommand):
  """Create a certificate."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          Create a new certificate.

          * Managed certificates can be created by supplying one or more domain names
            and an (optional) list of DNS authorizations for those domain names.
          * Self-managed certificates can be created by uploading a certificate
            and its corresponding private key (both in PEM format).
          """
      ),
      'EXAMPLES': (
          """\
          To create (upload) a self-managed certificate called `www-example-com`, run:

            $ {command} www-example-com --private-key-file=key.pem --certificate-file=cert.pem

          To create a certificate managed by Certificate Manager called `api-example-com`, run:

            $ {command} api-example-com --domains="api.example.com"

          To create a certificate managed by Certificate Manager called `api-example-com`, using an
          existing DNS authorization, run:

            $ {command} api-example-com --dns-authorizations=api-example-com \\
                --domains="api.example.com"
          """
      ),
      'API REFERENCE': (
          """\
          This command uses the certificatemanager/v1 API. The full documentation for this API can
          be found at: https://docs.cloud.google.com/certificate-manager/docs/overview
          """
      ),
  }

  @staticmethod
  def Args(parser):
    resource_args.AddCertificateResourceArg(parser, 'to create')
    flags.AddCertificateConfigFlagsToParser(parser)
    flags.AddAsyncFlagToParser(parser)
    flags.AddDescriptionFlagToParser(parser, 'certificate')
    labels_util.AddCreateLabelsFlags(parser)
    flags.AddScopeFlagToParser(parser)
    flags.AddTagsFlags(parser)

  def Run(self, args):
    client = certificates.CertificateClient()
    cert_ref = args.CONCEPTS.certificate.Parse()
    parent_ref = cert_ref.Parent()

    labels = labels_util.ParseCreateArgs(
        args, client.messages.Certificate.LabelsValue
    )
    tags = flags.GetTagsFromArgs(args, client.messages.Certificate.TagsValue)
    scope = flags.GetScopeFromArgs(
        args, client.messages.Certificate.ScopeValueValuesEnum
    )
    managed_cert_data = flags.GetManagedCertificateFromArgs(
        args, client.messages, parent_ref
    )
    self_managed_cert_data = flags.GetSelfManagedCertificateFromArgs(
        args, client.messages
    )

    response = client.Create(
        parent_ref,
        cert_ref.Name(),
        self_managed_cert_data=self_managed_cert_data,
        managed_cert_data=managed_cert_data,
        scope=scope,
        description=args.description,
        labels=labels,
        tags=tags,
    )
    return util.WaitForCertificateCreation(
        response, cert_ref, is_async=args.async_
    )
