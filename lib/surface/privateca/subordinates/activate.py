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
"""Activate a pending certificate authority."""

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import create_utils
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import iam
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import pem_utils
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Activate(base.SilentCommand):
  r"""Activate a subordinate certificate authority awaiting user activation.

  This command activates a subordinate Certificate Authority (CA) that has
  been created but is awaiting activation. To activate a CA either provide the
  path to an already-created PEM CA certificate and issuer chain, or specify
  the issuer's CA Pool to create the CA certificate now.

  ## EXAMPLES

  To activate a subordinate CA named 'server-tls-1' in the location 'us-west1'
  and CA Pool 'server-tls-pool' using a PEM certificate chain in 'chain.crt':

    $ {command} server-tls-1 \
      --location=us-west1 \
      --pool=server-tls-pool \
      --pem-chain=./chain.crt

  To activate a subordinate CA named 'server-tls-1' in the location 'us-west1'
  and CA Pool 'server-tls-pool' using an issuer CA Pool 'issuer-pool' in the
  same location:

    $ {command} server-tls-1 \
      --location=us-west1 \
      --pool=server-tls-pool \
      --issuer-pool=issuer-pool

  To activate a subordinate CA named 'server-tls-1' in the location 'us-west1'
  and CA Pool 'server-tls-pool' using a specific issuer CA 'issuer-ca-1' in the
  issuer CA Pool 'issuer-pool' in location 'us-east1':

    $ {command} server-tls-1 \
      --location=us-west1 \
      --pool=server-tls-pool \
      --issuer-pool=issuer-pool \
      --issuer-location=us-east1 \
      --issuer-ca=issuer-ca-1
  """

  def __init__(self, *args, **kwargs):
    super(Activate, self).__init__(*args, **kwargs)
    self.client = privateca_base.GetClientInstance(api_version='v1')
    self.messages = privateca_base.GetMessagesModule(api_version='v1')

  @staticmethod
  def Args(parser):
    resource_args.AddCertAuthorityPositionalResourceArg(parser, 'to activate')

    activation_group = parser.add_group(
        mutex=True,
        required=True,
        help='The activation method for the subordinate CA.',
    )

    base.Argument(
        '--pem-chain',
        help=(
            'A file containing a list of PEM-encoded certificates, starting '
            'with the current CA certificate and ending with the root CA '
            'certificate.'
        ),
    ).AddToParser(activation_group)

    issuing_resource_group = activation_group.add_group(
        mutex=False,
        help='The issuing resource used for this CA certificate.',
    )

    base.Argument(
        '--issuer-ca',
        help=(
            'The Certificate Authority ID of the CA to issue the subordinate '
            'CA certificate from. This ID is optional. If omitted, '
            'any available ENABLED CA in the issuing CA pool will be chosen.'
        ),
        required=False,
    ).AddToParser(issuing_resource_group)

    concept_parsers.ConceptParser([
        presentation_specs.ResourcePresentationSpec(
            '--issuer-pool',
            resource_args.CreateCaPoolResourceSpec('Issuer'),
            'The issuing CA Pool to use, if it is on Certificate Authority'
            ' Service.',
            prefixes=True,
            required=False,
            flag_name_overrides={
                'location': '--issuer-location',
            },
            group=issuing_resource_group,
        ),
    ]).AddToParser(parser)

    flags.AddAutoEnableFlag(parser)

  def _ParsePemChainFromFile(self, pem_chain_file):
    """Parses a pem chain from a file, splitting the leaf cert and chain.

    Args:
      pem_chain_file: file containing the pem_chain.

    Raises:
      exceptions.InvalidArgumentException if not enough certificates are
      included.

    Returns:
      A tuple with (leaf_cert, rest_of_chain)
    """
    try:
      pem_chain_input = files.ReadFileContents(pem_chain_file)
    except (files.Error, OSError, IOError):
      raise exceptions.BadFileException(
          "Could not read provided PEM chain file '{}'.".format(pem_chain_file)
      )

    certs = pem_utils.ValidateAndParsePemChain(pem_chain_input)
    if len(certs) < 2:
      raise exceptions.InvalidArgumentException(
          'pem-chain',
          'The pem_chain must include at least two certificates - the'
          ' subordinate CA certificate and an issuer certificate.',
      )

    return certs[0], certs[1:]

  def _EnableCertificateAuthority(self, ca_name):
    """Enables the given CA."""
    enable_request = self.messages.PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesEnableRequest(
        name=ca_name,
        enableCertificateAuthorityRequest=self.messages.EnableCertificateAuthorityRequest(
            requestId=request_utils.GenerateRequestId()
        ),
    )
    operation = (
        self.client.projects_locations_caPools_certificateAuthorities.Enable(
            enable_request
        )
    )
    return operations.Await(operation, 'Enabling CA.', api_version='v1')

  def _ShouldEnableCa(self, args, ca_ref):
    """Determines whether the CA should be enabled or not."""
    if args.auto_enable:
      return True

    # Return false if there already is an enabled CA in the pool.
    ca_pool_name = ca_ref.Parent().RelativeName()
    list_response = self.client.projects_locations_caPools_certificateAuthorities.List(
        self.messages.PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesListRequest(
            parent=ca_pool_name
        )
    )
    if create_utils.HasEnabledCa(
        list_response.certificateAuthorities, self.messages
    ):
      return False

    # Prompt the user if they would like to enable a CA in the pool.
    return console_io.PromptContinue(
        message=(
            'The CaPool [{}] has no enabled CAs and cannot issue any '
            'certificates until at least one CA is enabled. Would you like to '
            'also enable this CA?'.format(ca_ref.Parent().Name())
        ),
        default=False,
    )

  def Run(self, args):
    resource_args.ValidateResourceIsCompleteIfSpecified(args, 'issuer_pool')
    client = privateca_base.GetClientInstance(api_version='v1')
    messages = privateca_base.GetMessagesModule(api_version='v1')
    ca_ref = args.CONCEPTS.certificate_authority.Parse()

    if args.IsSpecified('pem_chain'):
      pem_cert, pem_chain = self._ParsePemChainFromFile(args.pem_chain)
    else:
      issuer_ref = args.CONCEPTS.issuer_pool.Parse()
      if not issuer_ref:
        raise exceptions.RequiredArgumentException(
            '--issuer-pool',
            'Issuer pool is required for first-party activation.',
        )

      ca = client.projects_locations_caPools_certificateAuthorities.Get(
          messages.PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesGetRequest(
              name=ca_ref.RelativeName()
          )
      )

      if (
          ca.state
          != messages.CertificateAuthority.StateValueValuesEnum.AWAITING_USER_ACTIVATION
      ):
        raise exceptions.InvalidArgumentException(
            'CERTIFICATE_AUTHORITY',
            'Certificate Authority [{}] is not in PENDING_ACTIVATION state'
            ' (current state is {}).'.format(ca_ref.Name(), ca.state),
        )

      iam.CheckCreateCertificatePermissions(issuer_ref)

      issuer_ca = args.issuer_ca if args.IsSpecified('issuer_ca') else None
      create_utils.ValidateIssuingPool(issuer_ref.RelativeName(), issuer_ca)

      csr_response = client.projects_locations_caPools_certificateAuthorities.Fetch(
          messages.PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesFetchRequest(
              name=ca_ref.RelativeName()
          )
      )
      csr = csr_response.pemCsr

      ca_certificate = create_utils.SignCsr(issuer_ref, csr, issuer_ca, ca)
      pem_cert = ca_certificate.pemCertificate
      pem_chain = ca_certificate.pemCertificateChain

    operation = client.projects_locations_caPools_certificateAuthorities.Activate(
        messages.PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesActivateRequest(
            name=ca_ref.RelativeName(),
            activateCertificateAuthorityRequest=messages.ActivateCertificateAuthorityRequest(
                pemCaCertificate=pem_cert,
                subordinateConfig=messages.SubordinateConfig(
                    pemIssuerChain=messages.SubordinateConfigChain(
                        pemCertificates=pem_chain
                    )
                ),
            ),
        )
    )

    operations.Await(
        operation, 'Activating Certificate Authority.', api_version='v1'
    )
    log.status.Print(
        'Activated Certificate Authority [{}].'.format(ca_ref.Name())
    )
    if self._ShouldEnableCa(args, ca_ref):
      self._EnableCertificateAuthority(ca_ref.RelativeName())
