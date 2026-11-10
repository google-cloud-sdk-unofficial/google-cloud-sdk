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
"""'software-delivery-trust settings binauthz-config update' command."""

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.software_delivery_trust import util
from googlecloudsdk.core import resources

_DETAILED_HELP = {
    'DESCRIPTION': (
        '{description}\n\n'
        'To replace the signing key for an existing gate:\n'
        '- Running `--remove-attestors` and `--add-attestor` on the same gate'
        ' in a single command modifies the gate in place.\n'
        '- Running `--remove-attestors` followed by `--add-attestor` in a'
        ' separate command deletes and recreates the gate.'
    ),
    'EXAMPLES': (
        """\
        To enable automatic publishing and configure attestors for prod and staging in location `us-central1`, run:

          $ {command} \\
              --location=us-central1 \\
              --publish-destination=container-analysis \\
              --add-attestor="gate=prod,signing-crypto-key-version=projects/my-project/locations/us-central1/keyRings/my-ring/cryptoKeys/prod-key/cryptoKeyVersions/1" \\
              --add-attestor="gate=staging,signing-crypto-key-version=projects/my-project/locations/us-central1/keyRings/my-ring/cryptoKeys/staging-key/cryptoKeyVersions/1"

        To disable automatic publishing in location `us-central1`, run:

          $ {command} \\
              --location=us-central1 \\
              --publish-destination=none

        To clear all configured attestors in location `us-central1`, run:

          $ {command} \\
              --location=us-central1 \\
              --clear-attestors
        """
    ),
}


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update a Binary Authorization trust config."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    util.AddLocationResourceArg(
        parser,
        'Location of the Software Delivery Trust settings.',
        required=True,
    )

    parser.add_argument(
        '--publish-destination',
        choices={
            'container-analysis': (
                'Automatically publish/revoke signed VSA occurrences in'
                ' Container Analysis.'
            ),
            'none': 'Disable automatic publishing.',
        },
        help=(
            'Destination where SD Trust automatically publishes signed VSAs'
            ' upon evaluation.'
        ),
    )

    attestor_group = parser.add_mutually_exclusive_group()
    incremental_group = attestor_group.add_group(
        help='Incremental attestor update flags.'
    )
    incremental_group.add_argument(
        '--add-attestor',
        action='append',
        type=arg_parsers.ArgDict(
            spec={
                'gate': str,
                'signing-crypto-key-version': str,
            },
            required_keys=['gate', 'signing-crypto-key-version'],
        ),
        metavar='gate=GATE,signing-crypto-key-version=KEY_VERSION',
        help=(
            'Key-value pair defining the lifecycle gate and asymmetric KMS'
            ' signing key version. Can be repeated. Attributes: gate:'
            ' Identifier of the gate corresponding to PolicyBinding'
            ' custom_gate (e.g., prod). signing-crypto-key-version: Cloud KMS'
            ' CryptoKeyVersion resource name. Fails if the gate already'
            ' exists; pass --remove-attestors and --add-attestor on the same'
            ' gate in a single command to modify in place, or in separate'
            ' commands to delete and recreate.'
        ),
    )
    incremental_group.add_argument(
        '--remove-attestors',
        '--remove-attestor',
        type=arg_parsers.ArgList(),
        metavar='GATE',
        help=(
            'Comma-separated list of gate identifiers to remove. Using'
            ' --remove-attestors and --add-attestor on the same gate in a'
            ' single command modifies it in place; using them in separate'
            ' commands deletes and recreates it.'
        ),
    )

    attestor_group.add_argument(
        '--clear-attestors',
        action='store_true',
        help='Clears all configured attestors.',
    )
    attestor_group.add_argument(
        '--attestors-file',
        metavar='FILE_PATH',
        help=(
            'Path to a local YAML or JSON file defining the complete list of'
            ' attestors.'
        ),
    )

    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    client = util.GetClient()
    messages = util.GetMessages()

    location_ref = args.CONCEPTS.location.Parse()
    settings_name = '{}/settings'.format(location_ref.RelativeName())

    has_publish_dest = args.IsSpecified('publish_destination')
    has_add_attestor = args.IsSpecified('add_attestor')
    has_remove_attestors = args.IsSpecified('remove_attestors')
    has_clear_attestors = (
        args.IsSpecified('clear_attestors') and args.clear_attestors
    )
    has_attestors_file = args.IsSpecified('attestors_file')

    has_attestor_changes = (
        has_add_attestor
        or has_remove_attestors
        or has_clear_attestors
        or has_attestors_file
    )

    if not has_publish_dest and not has_attestor_changes:
      raise exceptions.MinimumArgumentException(
          [
              '--publish-destination',
              '--add-attestor',
              '--remove-attestors',
              '--clear-attestors',
              '--attestors-file',
          ],
          'Please specify at least one property to update.',
      )

    update_mask = []
    binauthz_config = messages.BinaryAuthorizationConfig()

    # 1. Handle publish destination
    if has_publish_dest:
      update_mask.append('binary_authorization_config.publish_destination')
      if args.publish_destination == 'container-analysis':
        binauthz_config.publishDestination = (
            messages.BinaryAuthorizationConfig.PublishDestinationValueValuesEnum.CONTAINER_ANALYSIS
        )
      elif args.publish_destination == 'none':
        binauthz_config.publishDestination = (
            messages.BinaryAuthorizationConfig.PublishDestinationValueValuesEnum.PUBLISH_DESTINATION_UNSPECIFIED
        )

    # 2. Handle attestor updates
    if has_attestor_changes:
      update_mask.append('binary_authorization_config.attestors')
      if has_clear_attestors:
        binauthz_config.attestors = []
      elif has_attestors_file:
        binauthz_config.attestors = util.LoadAttestorsFromFile(
            args.attestors_file, messages
        )
      else:
        # Incremental update: read current settings first
        get_req = (
            messages.SoftwaredeliverytrustProjectsLocationsGetSettingsRequest(
                name=settings_name
            )
        )
        existing_settings = client.projects_locations.GetSettings(get_req)
        existing_attestors = []
        if (
            existing_settings
            and existing_settings.binaryAuthorizationConfig
            and existing_settings.binaryAuthorizationConfig.attestors
        ):
          existing_attestors = (
              existing_settings.binaryAuthorizationConfig.attestors
          )

        # Build map by normalized gate name
        attestors_map = {att.gate: att for att in existing_attestors}

        # Remove gates
        gates_to_remove = set()
        if has_remove_attestors:
          gates_to_remove.update(args.remove_attestors)
        for gate in gates_to_remove:
          normalized_gate = util.NormalizeGateName(gate)
          attestors_map.pop(normalized_gate, None)

        # Add attestors
        if has_add_attestor:
          for att_dict in args.add_attestor:
            gate = util.NormalizeGateName(att_dict.get('gate'))
            if gate in attestors_map:
              raise exceptions.InvalidArgumentException(
                  '--add-attestor',
                  'Attestor for gate "{0}" already exists. To update its'
                  ' signing key version:\n'
                  '  - Pass --remove-attestors={0} and --add-attestor in a'
                  ' single command to modify it in place.\n'
                  '  - Run --remove-attestors={0} first, followed by'
                  ' --add-attestor in a separate command to delete and recreate'
                  ' it.'.format(gate),
              )
            key_ver = att_dict.get(
                'signing-crypto-key-version'
            ) or att_dict.get('signing_crypto_key_version')
            attestors_map[gate] = messages.Attestor(
                gate=gate,
                signingCryptoKeyVersion=str(key_ver).strip(),
            )

        binauthz_config.attestors = list(attestors_map.values())

    settings_to_update = messages.Settings(
        name=settings_name,
        binaryAuthorizationConfig=binauthz_config,
    )
    req = messages.SoftwaredeliverytrustProjectsLocationsUpdateSettingsRequest(
        name=settings_name,
        settings=settings_to_update,
        updateMask=','.join(sorted(update_mask)),
    )
    operation = client.projects_locations.UpdateSettings(req)

    if args.async_:
      return operation

    poller = util.SettingsOperationPoller(client, messages, settings_name)
    if operation.done:
      if operation.error:
        raise waiter.OperationError(operation.error.message)
      return poller.GetResult(operation)

    operation_ref = resources.REGISTRY.Parse(
        operation.name,
        collection='softwaredeliverytrust.projects.locations.operations',
    )
    return waiter.WaitFor(
        poller,
        operation_ref,
        'Updating Software Delivery Trust settings for [{}]'.format(
            settings_name
        ),
    )
