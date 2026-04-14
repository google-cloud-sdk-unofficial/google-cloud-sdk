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


def CreateAssociationHook(unused_ref, args, request):
  """Constructs association path from reservation and block_name flags."""
  association = []
  if args.IsKnownAndSpecified('reservation') and args.reservation:
    association.append('reservations/{}'.format(args.reservation))
    if args.IsKnownAndSpecified('reservation_block') and args.reservation_block:
      block_name = args.reservation_block
    elif args.IsKnownAndSpecified('block_name') and args.block_name:
      block_name = args.block_name
    else:
      block_name = None

    if block_name:
      association.append('reservationBlocks/{}'.format(block_name))

  if association:
    request.association = '/'.join(association)
  return request
