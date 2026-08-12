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
"""Command for testing IAM permissions for SSL certificates."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_certificates import flags
from googlecloudsdk.command_lib.compute.ssl_certificates import ssl_certificates_utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class TestIamPermissions(base.Command):
  """Test IAM permissions for a Compute Engine SSL certificate."""

  SSL_CERTIFICATE_ARG = None

  @staticmethod
  def Args(parser):
    TestIamPermissions.SSL_CERTIFICATE_ARG = flags.SslCertificateArgument(
        global_help_text='(Default) If set, the SSL certificate is global.'
    )
    TestIamPermissions.SSL_CERTIFICATE_ARG.AddArgument(
        parser, operation_type='test-iam-permissions'
    )
    parser.add_argument(
        '--permissions',
        metavar='PERMISSION',
        type=arg_parsers.ArgList(),
        required=True,
        help='Permissions to be tested.',
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    ssl_certificate_ref = (
        TestIamPermissions.SSL_CERTIFICATE_ARG.ResolveAsResource(
            args,
            holder.resources,
            default_scope=compute_scope.ScopeEnum.GLOBAL,
            scope_lister=compute_flags.GetDefaultScopeLister(client),
        )
    )

    if ssl_certificates_utils.IsRegionalSslCertificatesRef(ssl_certificate_ref):
      service = client.apitools_client.regionSslCertificates
      request = (
          client.messages.ComputeRegionSslCertificatesTestIamPermissionsRequest(
              project=ssl_certificate_ref.project,
              region=ssl_certificate_ref.region,
              resource=ssl_certificate_ref.Name(),
              testPermissionsRequest=client.messages.TestPermissionsRequest(
                  permissions=args.permissions
              ),
          )
      )
    else:
      service = client.apitools_client.sslCertificates
      request = client.messages.ComputeSslCertificatesTestIamPermissionsRequest(
          project=ssl_certificate_ref.project,
          resource=ssl_certificate_ref.Name(),
          testPermissionsRequest=client.messages.TestPermissionsRequest(
              permissions=args.permissions
          ),
      )

    return client.MakeRequests([(service, 'TestIamPermissions', request)])[0]


TestIamPermissions.detailed_help = {
    'brief': 'Test IAM permissions for a Compute Engine SSL certificate.',
    'DESCRIPTION': """\
        *{command}* tests the IAM permissions that a caller has on a Compute
        Engine SSL certificate.
        """,
    'EXAMPLES': """\
        To test if the caller has the `compute.regionSslCertificates.get`
        permission on the regional SSL certificate `my-cert` in region `us-central1`,
        run:

          $ {command} my-cert --region=us-central1 --permissions=compute.regionSslCertificates.get

        To test if the caller has the `compute.sslCertificates.get`
        permission on the global SSL certificate `my-cert`, run:

          $ {command} my-cert --global --permissions=compute.sslCertificates.get
        """,
}
