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
"""The deprecated `gcloud saas-runtime` alias of `gcloud app-lifecycle-manager`.

This group has no commands of its own. gcloud_main.py maps a fixed set of
`app-lifecycle-manager` subgroups under it so existing scripts keep working.
The group is hidden, deprecated, and only registered on the ALPHA and BETA
tracks, so no GA `gcloud saas-runtime` surface is created when
`gcloud app-lifecycle-manager` goes GA.
"""

from googlecloudsdk.calliope import base

# TODO(b/497928442): Remove this group, and its mappings in gcloud_main.py,
# after a suitable deprecation period.
_DEPRECATION_WARNING = (
    'The `gcloud saas-runtime` commands have been renamed and will soon be '
    'removed. Please use `gcloud app-lifecycle-manager` instead.'
)


@base.Hidden
@base.Deprecate(is_removed=False, warning=_DEPRECATION_WARNING)
@base.UniverseCompatible
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class SaasRuntime(base.Group):
  category = base.SAAS_CATEGORY
  detailed_help = {'brief': 'Commands for App Lifecycle Manager.'}
