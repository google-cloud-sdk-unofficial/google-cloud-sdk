# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Update an ekmconnection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import certs
from googlecloudsdk.command_lib.kms import exceptions as kms_exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import resource_args


class Update(base.UpdateCommand):
  r"""Update an ekmconnection.

  {command} can be used to update the ekmconnection. Updates can be made to the
  ekmconnection's service resolver's fields.

  ## EXAMPLES

  The following command updates an ekm-connection named `laplace` service
  resolver's hostname within location `us-east1`:

  $ {command} laplace --location=us-east1 \
                      --hostname=newhostname.foo \

  The following command updates an ekm-connection named `laplace` service
  resolver's service_directory_service, endpoint_filter, hostname, and
  server_certificates within location `us-east1`:

    $ {command} laplace --location=us-east1 \
        --service-directory-service="foo" \
        --endpoint-filter="foo > bar" \
        --hostname="newhostname.foo" \
        --server-certificates-files=foo.pem,bar.pem

  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsEkmConnectionResourceArgForKMS(parser, True,
                                                       'ekm_connection')
    flags.AddServiceDirectoryServiceFlag(parser)
    flags.AddEndpointFilterFlag(parser)
    flags.AddHostnameFlag(parser)
    flags.AddServerCertificatesFilesFlag(parser)

  def CreateRequest(self, args, messages, previous_ekm_connection):
    ec_ref = flags.ParseEkmConnectionName(args)
    service_resolver_to_update = previous_ekm_connection.serviceResolvers[0]

    if args.service_directory_service:
      service_resolver_to_update.serviceDirectoryService = args.service_directory_service

    if args.endpoint_filter:
      service_resolver_to_update.endpointFilter = args.endpoint_filter

    if args.hostname:
      service_resolver_to_update.hostname = args.hostname

    certificate_list = []
    if args.server_certificates_files:
      for cert_file in args.server_certificates_files:
        try:
          certificate_list.append(
              messages.Certificate(rawDer=certs.GetDerCertificate(cert_file)))
        except Exception as e:
          raise exceptions.BadArgumentException(
              '--server-certificates-files',
              'Error while attempting to read file {} : {}'.format(
                  cert_file, e))
      service_resolver_to_update.serverCertificates = certificate_list

    req = messages.CloudkmsProjectsLocationsEkmConnectionsPatchRequest(
        name=ec_ref.RelativeName(),
        ekmConnection=messages.EkmConnection(
            serviceResolvers=[service_resolver_to_update]))

    req.updateMask = 'serviceResolvers'

    return req

  def Run(self, args):
    if not (args.service_directory_service or args.endpoint_filter or
            args.hostname or args.server_certificates_files):
      raise kms_exceptions.UpdateError(
          'An error occured: At least one of --service-directory-service or '
          '--endpoint-filter or --hostname or --server-certificates-files '
          'must be specified.')

    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    ec_ref = flags.ParseEkmConnectionName(args)

    # Try to get the ekmConnection and raise an exception if it doesn't exist.
    ekm_connection = client.projects_locations_ekmConnections.Get(
        messages.CloudkmsProjectsLocationsEkmConnectionsGetRequest(
            name=ec_ref.RelativeName()))

    # Make update request
    update_req = self.CreateRequest(args, messages, ekm_connection)

    return client.projects_locations_ekmConnections.Patch(update_req)
