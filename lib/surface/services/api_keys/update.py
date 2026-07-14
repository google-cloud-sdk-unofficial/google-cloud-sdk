# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""services api-keys update command."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
import dataclasses
import itertools
import types
from typing import Any, TypeVar

from googlecloudsdk.api_lib.services import apikeys
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import log

OP_BASE_CMD = 'gcloud services operations '
OP_WAIT_CMD = OP_BASE_CMD + 'wait {0}'
DETAILED_HELP = {
    'EXAMPLES': (
        """
        To remove all restrictions of the key:

          $ {command} projects/myproject/locations/global/keys/my-key-id --clear-restrictions

        To update display name and set allowed ips as server key restrictions:

          $ {command} projects/myproject/locations/global/keys/my-key-id --display-name="test name" --allowed-ips=2620:15c:2c4:203:2776:1f90:6b3b:217,104.133.8.78

        To update annotations:

          $ {command} projects/myproject/locations/global/keys/my-key-id --annotations=foo=bar,abc=def

        To update key's allowed referrers restriction:

          $ {command} projects/myproject/locations/global/keys/my-key-id --allowed-referrers="https://www.example.com/*,http://sub.example.com/*"

        To update key's allowed ios app bundle ids:

          $ {command} projects/myproject/locations/global/keys/my-key-id --allowed-bundle-ids=my.app

        To update key's allowed android application:

          $ {command} projects/myproject/locations/global/keys/my-key-id --allowed-application=sha1_fingerprint=foo1,package_name=bar1 --allowed-application=sha1_fingerprint=foo2,package_name=bar2

        To update keys' allowed api target with multiple services:

          $ {command} projects/myproject/locations/global/keys/my-key-id --api-target=service=bar.service.com --api-target=service=foo.service.com

        To update keys' allowed api target with service and method:

          $ {command} projects/myproject/locations/global/keys/my-key-id  --flags-file=my-flags.yaml

          The content of 'my-flags.yaml' is as following:

          ```
            - --api-target:
                service: "foo.service.com"
            - --api-target:
                service: "bar.service.com"
                methods:
                - "foomethod"
                - "barmethod"
            ```
        """
    )
}


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Update(base.UpdateCommand):
  """Update an API key's metadata."""

  @staticmethod
  def Args(parser):
    common_flags.key_flag(parser=parser, suffix='to update')
    common_flags.display_name_flag(parser=parser, suffix='to update')
    common_flags.add_key_update_args(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args: argparse.Namespace) -> Any:
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      None
    """

    client = apikeys.GetClientInstance()
    messages = client.MESSAGES_MODULE

    key_ref = args.CONCEPTS.key.Parse()
    update_mask = []
    key_proto = messages.V2Key(
        name=key_ref.RelativeName(), restrictions=messages.V2Restrictions()
    )
    if args.IsSpecified('annotations'):
      update_mask.append('annotations')
      key_proto.annotations = apikeys.GetAnnotations(args, messages)
    if args.IsSpecified('display_name'):
      update_mask.append('display_name')
      key_proto.displayName = args.display_name
    if args.IsSpecified('clear_annotations'):
      update_mask.append('annotations')
    if args.IsSpecified('clear_restrictions'):
      update_mask.append('restrictions')
    else:
      if args.IsSpecified('allowed_referrers'):
        update_mask.append('restrictions.browser_key_restrictions')
        key_proto.restrictions.browserKeyRestrictions = (
            messages.V2BrowserKeyRestrictions(
                allowedReferrers=args.allowed_referrers
            )
        )
      elif args.IsSpecified('allowed_ips'):
        update_mask.append('restrictions.server_key_restrictions')
        key_proto.restrictions.serverKeyRestrictions = (
            messages.V2ServerKeyRestrictions(allowedIps=args.allowed_ips)
        )
      elif args.IsSpecified('allowed_bundle_ids'):
        update_mask.append('restrictions.ios_key_restrictions')
        key_proto.restrictions.iosKeyRestrictions = (
            messages.V2IosKeyRestrictions(
                allowedBundleIds=args.allowed_bundle_ids
            )
        )
      elif args.IsSpecified('allowed_application'):
        update_mask.append('restrictions.android_key_restrictions')
        key_proto.restrictions.androidKeyRestrictions = (
            messages.V2AndroidKeyRestrictions(
                allowedApplications=apikeys.GetAllowedAndroidApplications(
                    args, messages
                )
            )
        )
      if args.IsSpecified('api_target'):
        update_mask.append('restrictions.api_targets')
        key_proto.restrictions.apiTargets = apikeys.GetApiTargets(
            args, messages
        )
    request = messages.ApikeysProjectsLocationsKeysPatchRequest(
        name=key_ref.RelativeName(),
        updateMask=','.join(update_mask),
        v2Key=key_proto,
    )
    op = client.projects_locations_keys.Patch(request)
    if not op.done:
      if args.async_:
        cmd = OP_WAIT_CMD.format(op.name)
        log.status.Print(
            f'Asynchronous operation is in progress... Use the following '
            f'command to wait for its completion:\n {cmd}'
        )
        return op
      op = services_util.WaitOperation(op.name, apikeys.GetOperation)
    services_util.PrintOperationWithResponse(op)
    return op

  detailed_help = DETAILED_HELP


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaUpdate(Update):
  """A surface for updating API keys, including append support."""

  @classmethod
  def Args(cls, parser):
    """Add arguments to the parser.

    Args:
      parser: The argparse.ArgumentParser to which the arguments are added.
    """
    Update.Args(parser)
    parser.add_argument(
        '--append',
        action='store_true',
        help=(
            'If specified, merge the new restrictions with the current '
            'restrictions of the key instead of replacing them.'
        ),
    )

  def Run(self, args: argparse.Namespace) -> Any:
    """Run the update command for Alpha release track.

    This method extends the base Update.Run to support the '--append' flag,
    which allows merging new restrictions with existing ones instead of
    replacing them.

    Args:
      args: An argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The LRO object.

    Raises:
      googlecloudsdk.calliope.exceptions.InvalidArgumentException:
        If the --clear-restrictions flag is specified, if the updated key
        lacks API target restrictions, or if attempting to append a different
        client restriction type than already exists on the key.
    """
    client = apikeys.GetClientInstance(self.ReleaseTrack())
    messages = client.MESSAGES_MODULE
    key_ref = args.CONCEPTS.key.Parse()
    request = messages.ApikeysProjectsLocationsKeysGetRequest(
        name=key_ref.RelativeName()
    )
    current_key = client.projects_locations_keys.Get(request)

    current_has_api_targets = (
        current_key.restrictions is not None
        and current_key.restrictions.apiTargets
    )
    is_clearing = args.IsSpecified('clear_restrictions')
    is_specifying_api_target = args.IsSpecified('api_target')

    if is_clearing:
      raise exceptions.InvalidArgumentException(
          '--clear-restrictions',
          'The --clear-restrictions flag is not supported on the ALPHA track.',
      )

    if not (current_has_api_targets or is_specifying_api_target):
      raise exceptions.InvalidArgumentException(
          '--api-target',
          'API keys must have API target restrictions. Please specify '
          '`--api-target` to restrict this key.',
      )

    if not args.append:
      return super(AlphaUpdate, self).Run(args)

    update_mask = []
    key_proto = messages.V2Key(
        name=key_ref.RelativeName(), restrictions=messages.V2Restrictions()
    )

    if args.IsSpecified('annotations'):
      update_mask.append('annotations')
      key_proto.annotations = apikeys.GetAnnotations(args, messages)
    if args.IsSpecified('display_name'):
      update_mask.append('display_name')
      key_proto.displayName = args.display_name
    if args.IsSpecified('clear_annotations'):
      update_mask.append('annotations')

    # Copy etag from current key to ensure the update is based on the
    # latest version, preventing race conditions.
    if current_key.etag:
      key_proto.etag = current_key.etag

    current_restrictions = getattr(current_key, 'restrictions', None)
    current_client_type = _GetClientRestrictionType(current_restrictions)

    new_client_type = None
    if args.IsSpecified('allowed_referrers'):
      new_client_type = 'browserKeyRestrictions'
    elif args.IsSpecified('allowed_ips'):
      new_client_type = 'serverKeyRestrictions'
    elif args.IsSpecified('allowed_bundle_ids'):
      new_client_type = 'iosKeyRestrictions'
    elif args.IsSpecified('allowed_application'):
      new_client_type = 'androidKeyRestrictions'

    if (
        new_client_type
        and current_client_type
        and current_client_type != new_client_type
    ):
      new_friendly = _FRIENDLY_NAME_BY_TYPE[new_client_type]
      current_friendly = _FRIENDLY_NAME_BY_TYPE[current_client_type]
      raise exceptions.InvalidArgumentException(
          f'--{new_friendly}',
          f'Cannot append {new_friendly} restriction because the key already '
          f'has {current_friendly} restriction.',
      )

    if new_client_type:
      field_name, restriction_msg, mask_path = _GetMergedApplicationRestriction(
          current_restrictions, new_client_type, args, messages
      )
      setattr(key_proto.restrictions, field_name, restriction_msg)
      update_mask.append(mask_path)

    if args.IsSpecified('api_target'):
      current_api_targets = (
          getattr(current_restrictions, 'apiTargets', [])
          if current_restrictions
          else []
      )
      if current_api_targets is None:
        current_api_targets = []
      new_api_targets = apikeys.GetApiTargets(args, messages) or []
      merged_targets = _MergeApiTargets(
          current_api_targets, new_api_targets, messages
      )

      key_proto.restrictions.apiTargets = merged_targets
      update_mask.append('restrictions.api_targets')

    # Construct and send the patch request.
    request = messages.ApikeysProjectsLocationsKeysPatchRequest(
        name=key_ref.RelativeName(),
        updateMask=','.join(update_mask),
        v2Key=key_proto,
    )
    op = client.projects_locations_keys.Patch(request)
    if not op.done:
      if args.async_:
        cmd = OP_WAIT_CMD.format(op.name)
        log.status.Print(
            f'Asynchronous operation is in progress... Use the following '
            f'command to wait for its completion:\n {cmd}'
        )
        return op
      op = services_util.WaitOperation(op.name, apikeys.GetOperation)
    services_util.PrintOperationWithResponse(op)
    return op


@dataclasses.dataclass
class _ApiTargetEntry:
  """A structured record representing a parsed API target service.

  Attributes:
    service: The display service name of the target.
    methods: The list of methods allowed for this target.
    all_allowed: True if all methods are allowed for this service.
  """
  service: str
  methods: list[str]
  all_allowed: bool


def _GetAndroidAppKey(app: Any) -> tuple[str, str]:
  """Returns a package/fingerprint tuple representing an Android app."""
  pkg = getattr(app, 'packageName', '') or ''
  fingerprint = _NormalizeSha1(getattr(app, 'sha1Fingerprint', ''))
  return (pkg.strip(), fingerprint)


def _GetApiTargetMethods(target: Any) -> list[str]:
  """Returns a list of methods allowed for an API target."""
  return list(getattr(target, 'methods', None) or [])


# TODO(b/517632542): This method assumes client restrictions are mutually
# exclusive. This will need to be updated when API V3 is integrated,
# which supports multiple restriction types.
def _GetClientRestrictionType(restrictions: Any | None) -> str | None:
  """Returns the active application restriction type string from current restrictions.

  Args:
    restrictions: The key's restrictions protobuf message.

  Returns:
    The active restriction field name (str) or None if not set.
  """
  if restrictions is None:
    return None
  browser_key_restrictions = getattr(
      restrictions, 'browserKeyRestrictions', None
  )
  if (
      browser_key_restrictions is not None
      and getattr(browser_key_restrictions, 'allowedReferrers', None)
      is not None
  ):
    return 'browserKeyRestrictions'
  server_key_restrictions = getattr(restrictions, 'serverKeyRestrictions', None)
  if (
      server_key_restrictions is not None
      and getattr(server_key_restrictions, 'allowedIps', None) is not None
  ):
    return 'serverKeyRestrictions'
  ios_key_restrictions = getattr(restrictions, 'iosKeyRestrictions', None)
  if (
      ios_key_restrictions is not None
      and getattr(ios_key_restrictions, 'allowedBundleIds', None) is not None
  ):
    return 'iosKeyRestrictions'
  android_key_restrictions = getattr(
      restrictions, 'androidKeyRestrictions', None
  )
  if (
      android_key_restrictions is not None
      and getattr(android_key_restrictions, 'allowedApplications', None)
      is not None
  ):
    return 'androidKeyRestrictions'
  return None


def _NormalizeSha1(fingerprint: str | None) -> str:
  """Normalizes a SHA-1 fingerprint by stripping colons and spaces.

  Args:
    fingerprint: The raw fingerprint string to normalize.

  Returns:
    The normalized lowercase fingerprint (str).
  """
  if fingerprint is None:
    return ''
  return fingerprint.replace(':', '').replace(' ', '').lower()


_T = TypeVar('_T')


def _UnionPreservingOrder(
    current_list: Sequence[_T] | None,
    new_list: Sequence[_T] | None,
    key_fn: Callable[[_T], Any] = lambda x: x,
) -> list[_T]:
  """Unions two lists while preserving original insertion order.

  Args:
    current_list: The existing list.
    new_list: The new list to append.
    key_fn: A function to derive the comparison key for each item.

  Returns:
    A deduplicated union list preserving original insertion order.
  """
  seen = set()
  result = []
  for item in itertools.chain(current_list or [], new_list or []):
    if item is not None:
      key = key_fn(item)
      if key not in seen:
        seen.add(key)
        result.append(item)
  return result


def _GetMergedApplicationRestriction(
    current_restrictions: Any | None,
    client_type: str,
    args: argparse.Namespace,
    messages: Any,
) -> tuple[str, Any, str]:
  """Merges current and new application restrictions.

  Args:
    current_restrictions: The current V2Restrictions message.
    client_type: The client restriction type string.
    args: The argparse namespace.
    messages: The API client messages module.

  Returns:
    A tuple of (field_name, restriction_message, update_mask_path).
  """
  if client_type == 'browserKeyRestrictions':
    current_browser = (
        getattr(current_restrictions, 'browserKeyRestrictions', None)
        if current_restrictions is not None
        else None
    )
    current_list = (
        getattr(current_browser, 'allowedReferrers', [])
        if current_browser is not None
        else []
    )
    if current_list is None:
      current_list = []
    new_list = args.allowed_referrers or []
    merged_list = _UnionPreservingOrder(current_list, new_list)
    return (
        'browserKeyRestrictions',
        messages.V2BrowserKeyRestrictions(allowedReferrers=merged_list),
        'restrictions.browser_key_restrictions',
    )

  if client_type == 'serverKeyRestrictions':
    current_server = (
        getattr(current_restrictions, 'serverKeyRestrictions', None)
        if current_restrictions is not None
        else None
    )
    current_list = (
        getattr(current_server, 'allowedIps', [])
        if current_server is not None
        else []
    )
    if current_list is None:
      current_list = []
    new_list = args.allowed_ips or []
    merged_list = _UnionPreservingOrder(current_list, new_list)
    return (
        'serverKeyRestrictions',
        messages.V2ServerKeyRestrictions(allowedIps=merged_list),
        'restrictions.server_key_restrictions',
    )

  if client_type == 'iosKeyRestrictions':
    current_ios = (
        getattr(current_restrictions, 'iosKeyRestrictions', None)
        if current_restrictions is not None
        else None
    )
    current_list = (
        getattr(current_ios, 'allowedBundleIds', [])
        if current_ios is not None
        else []
    )
    if current_list is None:
      current_list = []
    new_list = args.allowed_bundle_ids or []
    merged_list = _UnionPreservingOrder(current_list, new_list)
    return (
        'iosKeyRestrictions',
        messages.V2IosKeyRestrictions(allowedBundleIds=merged_list),
        'restrictions.ios_key_restrictions',
    )

  if client_type == 'androidKeyRestrictions':
    current_android = (
        getattr(current_restrictions, 'androidKeyRestrictions', None)
        if current_restrictions is not None
        else None
    )
    current_list = (
        getattr(current_android, 'allowedApplications', [])
        if current_android is not None
        else []
    )
    if current_list is None:
      current_list = []
    new_list = apikeys.GetAllowedAndroidApplications(args, messages) or []
    merged_list = _UnionPreservingOrder(
        current_list, new_list, key_fn=_GetAndroidAppKey
    )
    return (
        'androidKeyRestrictions',
        messages.V2AndroidKeyRestrictions(allowedApplications=merged_list),
        'restrictions.android_key_restrictions',
    )

  raise ValueError(f'Unknown client type: {client_type}')


def _MergeApiTargets(
    current_targets: Sequence[Any] | None,
    new_targets: Sequence[Any] | None,
    messages: Any,
) -> list[Any]:
  """Merges current and new API target configurations by service.

  Args:
    current_targets: The list of current V2ApiTarget messages.
    new_targets: The list of new V2ApiTarget messages.
    messages: The API client messages module.

  Returns:
    A list of merged V2ApiTarget messages.
  """
  target_map = {}
  ordered_services: list[str] = []

  for target in current_targets or []:
    if target is None or getattr(target, 'service', None) is None:
      continue
    srv = target.service
    srv_lower = srv.lower()
    if srv_lower not in target_map:
      ordered_services.append(srv_lower)
    target_map[srv_lower] = _ApiTargetEntry(
        service=srv,
        methods=_GetApiTargetMethods(target),
        all_allowed=not getattr(target, 'methods', None),
    )

  for target in new_targets or []:
    if target is None or getattr(target, 'service', None) is None:
      continue
    srv = target.service
    srv_lower = srv.lower()
    new_methods = _GetApiTargetMethods(target)
    new_all_allowed = not getattr(target, 'methods', None)

    entry = target_map.get(srv_lower)
    if entry is not None:
      if entry.all_allowed or new_all_allowed:
        entry.all_allowed = True
        entry.methods = []
      else:
        entry.methods = _UnionPreservingOrder(
            entry.methods, new_methods, key_fn=lambda x: x.lower()
        )
    else:
      ordered_services.append(srv_lower)
      target_map[srv_lower] = _ApiTargetEntry(
          service=srv,
          methods=new_methods,
          all_allowed=new_all_allowed,
      )

  return [
      messages.V2ApiTarget(
          service=target_map[srv_lower].service,
          methods=(
              target_map[srv_lower].methods
              if not target_map[srv_lower].all_allowed
              else []
          ),
      )
      for srv_lower in ordered_services
  ]


_FRIENDLY_NAME_BY_TYPE = types.MappingProxyType({
    'browserKeyRestrictions': 'allowed-referrers',
    'serverKeyRestrictions': 'allowed-ips',
    'iosKeyRestrictions': 'allowed-bundle-ids',
    'androidKeyRestrictions': 'allowed-application',
})
