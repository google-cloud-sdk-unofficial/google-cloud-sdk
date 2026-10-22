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
"""Shared flags for Certificate Manager commands."""


from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.certificate_manager import hooks
from googlecloudsdk.command_lib.util.apis import arg_utils


def AddAsyncFlagToParser(parser):
  """Adds async flag. It's not marked as go/gcloud-style#commonly-used-flags."""
  base.ASYNC_FLAG.AddToParser(parser)


def AddDescriptionFlagToParser(parser, resource_name):
  """Adds description flag."""
  base.Argument(
      '--description',
      help='Text description of a {}.'.format(resource_name),
      category=base.COMMONLY_USED_FLAGS).AddToParser(parser)


def AddMapEntryMatcherFlagsToParser(parser):
  """Adds flags defining certificate map entry matcher."""
  is_primary_flag = base.Argument(
      '--set-primary',
      help='The certificate will be used as the default cert if no other certificate in the map matches on SNI.',
      action='store_true')
  hostname_flag = base.Argument(
      '--hostname',
      help='A domain name (FQDN), which controls when list of certificates specified in the resource will be taken under consideration for certificate selection.'
  )
  group = base.ArgumentGroup(
      help='Arguments to configure matcher for the certificate map entry.',
      required=True,
      mutex=True,
      category=base.COMMONLY_USED_FLAGS)
  group.AddArgument(is_primary_flag)
  group.AddArgument(hostname_flag)
  group.AddToParser(parser)


def AddSelfManagedCertificateDataFlagsToParser(parser, is_required):
  """Adds certificate file and private key file flags."""
  # If the group itself is not required, the command will fail if
  # 1. any argument in the group is provided and
  # 2. any required argument in the group is not provided.
  cert_flag = base.Argument(
      '--certificate-file',
      help='The certificate data in PEM-encoded form.',
      type=arg_parsers.FileContents(),
      required=True)
  key_flag = base.Argument(
      '--private-key-file',
      help='The private key data in PEM-encoded form.',
      type=arg_parsers.FileContents(),
      required=True)

  group = base.ArgumentGroup(
      help='Arguments to configure self-managed certificate data.',
      required=is_required,
      category=base.COMMONLY_USED_FLAGS if not is_required else None)
  group.AddArgument(cert_flag)
  group.AddArgument(key_flag)
  group.AddToParser(parser)


def GetSelfManagedCertificateFromArgs(args, messages):
  """Constructs SelfManagedCertificate message from args."""
  if not (
      args.IsSpecified('certificate_file')
      and args.IsSpecified('private_key_file')
  ):
    return None

  return messages.SelfManagedCertificate(
      pemCertificate=args.certificate_file.encode('utf-8'),
      pemPrivateKey=args.private_key_file.encode('utf-8'),
  )


def GetTags(parser):
  """Makes the base.Argument for --tags flag."""
  help_parts = [
      'List of tags KEY=VALUE pairs to bind.',
      'Each item must be expressed as',
      '`<tag-key-namespaced-name>=<tag-value-short-name>`.\n',
      'Example: `123/environment=production,123/costCenter=marketing`\n',
  ]
  base.Argument(
      '--tags',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      help='\n'.join(help_parts),
  ).AddToParser(parser)


def AddTagsFlags(parser):
  """Adds create command tags flags to an argparse parser.

  Args:
    parser: The argparse parser to add the flags to.
  """
  GetTags(parser)


def GetTagsFromArgs(args, tags_message, tags_arg_name='tags'):
  """Makes the tags message object."""
  tags = getattr(args, tags_arg_name)
  if not tags:
    return None
  # Sorted for test stability
  return tags_message(additionalProperties=[
      tags_message.AdditionalProperty(key=key, value=value)
      for key, value in sorted(tags.items())])


def AddScopeFlagToParser(parser):
  """Adds scope flag to parser."""
  scope_arg = base.ChoiceArgument(
      '--scope',
      choices={
          'default': (
              'Certificates with DEFAULT scope are used for Load Balancing and'
              ' Cloud CDN.\n\nIf unsure, choose this option.\n'
          ),
          'edge-cache': (
              'Certificates with scope EDGE_CACHE are special-purposed'
              ' certificates, scoped for use with Media Edge services only.\n'
          ),
          'all-regions': (
              'Certificates with scope ALL_REGIONS are currently used for'
              ' Cross-region Internal Application Load Balancer only.\n'
          ),
          'client-auth': (
              'Certificates with scope CLIENT_AUTH are used for client'
              ' authentication.\n'
          ),
      },
      default='DEFAULT',
      help_str=(
          'Scope of the managed certificate. This determines which services the'
          ' certificate can be attached to/associated with. Defaults to'
          ' `DEFAULT`.'
      ),
  )
  scope_arg.AddToParser(parser)


def GetScopeFromArgs(args, scope_enum):
  """Returns the apitools enum value for the scope flag."""
  scope = getattr(args, 'scope', None)
  if not scope:
    return scope_enum.DEFAULT
  return arg_utils.ChoiceToEnum(scope, scope_enum)


def AddCertificateConfigFlagsToParser(parser):
  """Adds flags for managed or self-managed certificate configuration."""
  root_group = base.ArgumentGroup(
      mutex=True,
      required=True,
      help=(
          'Configuration for creating and uploading certificates to Cloud'
          ' Certificate Manager.'
      ),
  )

  managed_group = base.ArgumentGroup(
      help='Configuration for creating new managed certificates.'
  )
  managed_group.AddArgument(
      base.Argument(
          '--domains',
          type=arg_parsers.ArgList(),
          metavar='DOMAINS',
          action=arg_parsers.UpdateAction,
          required=True,
          help=(
              'Public domain name(s) to create a certificate for.\n\n'
              '* If a DNS authorization is provided for the domain, the'
              ' certificate will be validated against the DNS record you added'
              ' as part of the authorization flow.\n* If no DNS authorization'
              ' is provided, Certificate Manager will attempt to validate the'
              ' domain against the serving endpoint directly.\n\nYou may list'
              ' multiple, comma-separated domain names to include multiple'
              ' names as Subject Alternative Names on the issued certificate.'
          ),
      )
  )

  auth_group = base.ArgumentGroup(mutex=True)
  auth_group.AddArgument(
      base.Argument(
          '--dns-authorizations',
          type=arg_parsers.ArgList(),
          metavar='DNS_AUTHORIZATIONS',
          action=arg_parsers.FlattenAction(dedup=False),
          help=(
              'Name(s) of the DNS authorizations for each listed'
              ' domain.\n\nNote that each domain requires a matching'
              ' authorization, and any domain that fails authorization will'
              ' prevent issuance and/or renewal of the certificate.\n\nTo'
              ' reference multiple DNS authorizations, provide a list of comma'
              ' separated DNS authorization resource names or URLs. For'
              ' example:\n\n $ {command}'
              ' --dns-authorizations=api-example-com,www-example-com'
          ),
      )
  )
  auth_group.AddArgument(
      base.Argument(
          '--issuance-config',
          help='Name of the Certificate Issuance Config to use for issuance.',
      )
  )
  managed_group.AddArgument(auth_group)

  self_managed_group = base.ArgumentGroup(
      help='Configuration for uploading self-managed certificates and keys.'
  )
  self_managed_group.AddArgument(
      base.Argument(
          '--certificate-file',
          type=arg_parsers.FileContents(),
          required=True,
          help='Certificate data in PEM-encoded form.',
      )
  )
  self_managed_group.AddArgument(
      base.Argument(
          '--private-key-file',
          type=arg_parsers.FileContents(),
          required=True,
          help='Private key data in PEM-encoded form.',
      )
  )

  root_group.AddArgument(managed_group)
  root_group.AddArgument(self_managed_group)
  root_group.AddToParser(parser)


def GetManagedCertificateFromArgs(args, messages, parent_ref):
  """Constructs ManagedCertificate message from args."""
  if not (
      args.IsSpecified('domains')
      or args.IsSpecified('dns_authorizations')
      or args.IsSpecified('issuance_config')
  ):
    return None

  kwargs = {}
  if getattr(args, 'domains', None) is not None:
    kwargs['domains'] = args.domains

  if getattr(args, 'dns_authorizations', None):
    dns_authorizations = []
    for auth in args.dns_authorizations:
      if not auth.startswith('projects/'):
        dns_authorizations.append(
            hooks.DNS_AUTHORIZATIONS_TEMPLATE.format(
                parent_ref.RelativeName(), auth
            )
        )
      else:
        dns_authorizations.append(auth)
    kwargs['dnsAuthorizations'] = dns_authorizations

  if getattr(args, 'issuance_config', None) is not None:
    if not args.issuance_config.startswith('projects/'):
      kwargs['issuanceConfig'] = hooks.ISSUANCE_CONFIG_TEMPLATE.format(
          parent_ref.RelativeName(), args.issuance_config
      )
    else:
      kwargs['issuanceConfig'] = args.issuance_config

  return messages.ManagedCertificate(**kwargs)
