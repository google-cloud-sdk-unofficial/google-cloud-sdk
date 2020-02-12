# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Describe a certificate."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import resource_args


class Describe(base.DescribeCommand):
  r"""Get metadata for a certificate.

  Returns metadata for the given certificate.

  ## EXAMPLES

  To get metadata for the 'frontend-server-tls' certificate:

    $ {command} frontend-server-tls \
      --issuer server-tls-1 --issuer-location us

  To download the PEM-encoded certificate for the 'frontend-server-tls'
  certificate to a file
  called 'frontend-server-tls.crt':

    $ {command} frontend-server-tls \
      --issuer server-tls-1 --issuer-location us \
      --format "value(pem_cert)" > ./frontend-server-tls.crt
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertificatePositionalResourceArg(parser, 'to describe')
    parser.display_info.AddFormat("""yaml(
        name,
        certificate_description.subject_description.hex_serial_number,
        certificate_description.subject_description.not_before_time,
        certificate_description.subject_description.not_after_time,
        revocation_details
    )
    """)

  def Run(self, args):
    client = privateca_base.GetClientInstance()
    messages = privateca_base.GetMessagesModule()
    cert_ref = args.CONCEPTS.certificate.Parse()

    return client.projects_locations_certificateAuthorities_certificates.Get(
        messages
        .PrivatecaProjectsLocationsCertificateAuthoritiesCertificatesGetRequest(
            name=cert_ref.RelativeName()))
