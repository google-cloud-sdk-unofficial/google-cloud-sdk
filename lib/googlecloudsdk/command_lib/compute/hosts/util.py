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
"""Hooks for compute hosts commands."""

from googlecloudsdk.calliope import exceptions


def CreateAssociationHook(unused_ref, args, request):
  """Constructs association path from reservation, reservation_block, and reservation_subblock flags."""

  # If user explicitly specified association, use it.
  if args.IsKnownAndSpecified('association') and args.association:
    request.association = args.association
    return request

  block_name_specified = (
      args.IsKnownAndSpecified('reservation_block') and args.reservation_block
  )

  subblock_name_specified = (
      args.IsKnownAndSpecified('reservation_subblock')
      and args.reservation_subblock
  )

  reservation_specified = (
      args.IsKnownAndSpecified('reservation') and args.reservation
  )

  if block_name_specified and not reservation_specified:
    raise exceptions.RequiredArgumentException(
        '--reservation',
        'Must be specified when --reservation-block is provided.',
    )

  if subblock_name_specified and not block_name_specified:
    raise exceptions.RequiredArgumentException(
        '--reservation-block',
        'Must be specified when --reservation-subblock is provided.',
    )

  association = []
  if reservation_specified:
    association.append(f'reservations/{args.reservation}')

  if block_name_specified:
    association.append(f'reservationBlocks/{args.reservation_block}')

  if subblock_name_specified:
    association.append(f'reservationSubBlocks/{args.reservation_subblock}')

  if association:
    request.association = '/'.join(association)
  else:
    request.association = ''

  return request
