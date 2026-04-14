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
"""Hooks for BigLake CLI."""

from googlecloudsdk.calliope import exceptions


def ValidateCatalogUpdateArgs(ref, args, req):
  """Checks that at least one update flag is specified."""
  del ref
  if not (args.IsSpecified('description')):
    raise exceptions.MinimumArgumentException(
        ['--description'],
        'At least one argument is required to update the catalog',
    )
  return req


def ValidateDatabaseUpdateArgs(ref, args, req):
  """Checks that at least one update flag is specified."""
  del ref
  if not (
      args.IsSpecified('location_uri')
      or args.IsSpecified('description')
      or args.IsSpecified('parameters')
  ):
    raise exceptions.MinimumArgumentException(
        ['--location-uri', '--description', '--parameters'],
        'At least one argument is required to update the database',
    )
  return req
