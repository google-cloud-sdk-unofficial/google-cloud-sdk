# Lint as: python3
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
"""Revoke a certificate."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import certificate_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core.util import times


class Revoke(base.SilentCommand):
  r"""Revoke a certificate.

  Revokes the given certificate for the given reason.

  ## EXAMPLES

  To revoke the 'frontend-server-tls' certificate due to key compromise:

    $ {command} --certificate-id frontend-server-tls \
      --issuer server-tls-1 --issuer-location us \
      --reason key_compromise

  To revoke the a certificate with the serial number
  '7B1E676A36BB90D01200000000AFF09C' due to a newer one being issued:

    $ {command} \
      --serial-number 7B1E676A36BB90D01200000000AFF09C \
      --issuer server-tls-1 --issuer-location us \
      --reason superseded
  """

  @staticmethod
  def Args(parser):
    id_group = parser.add_group(
        mutex=True, required=True, help='The certificate identifier.')
    serial_num_group = id_group.add_group(
        help='The serial number and certificate authority resource.',
        required=False)
    serial_num_group.add_argument(
        '--serial-number',
        help='The serial number of the certificate.',
        required=True)
    concept_parsers.ConceptParser([
        presentation_specs.ResourcePresentationSpec(
            '--certificate',
            resource_args.CreateCertificateResourceSpec('CERTIFICATE'),
            'The certificate to revoke.',
            required=False,
            prefixes=True,
            group=id_group),
        presentation_specs.ResourcePresentationSpec(
            '--issuer',
            resource_args.CreateCertificateAuthorityResourceSpec(
                'CERTIFICATE_AUTHORITY', 'issuer', 'issuer-location'),
            'The issuing certificate authority of the certificate to revoke.',
            required=False,
            group=serial_num_group),
    ]).AddToParser(parser)

    flags.AddRevocationReasonFlag(parser)

  def CheckCompleteResourceFlag(self, args, resource_attributes):
    """Validates that the resource, if specified, is complete.

    Args:
      args: The command arguments, parsed.
      resource_attributes: The attributes to check modal group properties on.
    """
    for attribute in resource_attributes:
      if not args.IsSpecified(attribute):
        continue

      for other_attribute in resource_attributes:
        if attribute != other_attribute and not args.IsSpecified(
            other_attribute):
          raise exceptions.InvalidArgumentException(
              attribute, '{} must be specified if {} is specified.'.format(
                  other_attribute.replace('_', '-'),
                  attribute.replace('_', '-')))

  def Run(self, args):
    cert_ref = args.CONCEPTS.certificate.Parse()
    if cert_ref:
      cert_name = cert_ref.RelativeName()
    else:
      # Check to make sure the certificate was not partially provided.
      self.CheckCompleteResourceFlag(
          args,
          ['certificate', 'certificate_issuer', 'certificate_issuer_location'])
      ca_ref = args.CONCEPTS.issuer.Parse()
      if not ca_ref:
        # Check to make sure the certificate authority was not partially
        # provided.
        self.CheckCompleteResourceFlag(args, ['issuer', 'issuer_location'])
        raise exceptions.Invalid.ArgumentException(
            '--issuer', 'Expected a value for the issuer.')
      cert_name = certificate_utils.GetCertificateBySerialNum(
          ca_ref, args.serial_number).name

    reason = flags.ParseRevocationChoiceToEnum(args.reason)

    client = privateca_base.GetClientInstance()
    messages = privateca_base.GetMessagesModule()

    operation = client.projects_locations_certificateAuthorities_certificates.Revoke(
        messages.
        PrivatecaProjectsLocationsCertificateAuthoritiesCertificatesRevokeRequest(
            name=cert_name,
            revokeCertificateRequest=messages.RevokeCertificateRequest(
                reason=reason)))

    response = operations.Await(operation, 'Revoking Certificate.')
    certificate = operations.GetMessageFromResponse(response,
                                                    messages.Certificate)

    revoke_time = times.ParseDateTime(
        certificate.revocationDetails.revocationTime)
    log.Print('Revoked certificate at {}.'.format(
        times.FormatDateTime(revoke_time, tzinfo=times.LOCAL)))
