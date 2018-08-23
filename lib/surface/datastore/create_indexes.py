# -*- coding: utf-8 -*- #
# Copyright 2013 Google Inc. All Rights Reserved.
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

"""The gcloud datstore create-indexes command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from surface.datastore.indexes import create

_DEPRECATION_WARNING = """\
`create-indexes` is deprecated. Please use `gcloud datastore indexes create` instead.
"""


# TODO(b/112529035): Clean up this command after 3 months of deprecation.
@base.Deprecate(is_removed=False, warning=_DEPRECATION_WARNING)
@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateIndexes(create.Create):
  """Create Datastore indexes."""
