# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""Commands for creating or manipulating dedicated L2 forwarding attachments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class InterconnectAttachments(base.Group):
  """Create or manipulate dedicated interconnect attachments."""
  pass

InterconnectAttachments.detailed_help = {
    'DESCRIPTION': """
        Create or manipulate L2 Forwarding Interconnect attachments.

        For more information about about interconnect attachments for L2
        Forwaring Interconnect, see the documentation for
        [L2 Forwarding interconnect attachments](https://cloud.google.com/network-connectivity/docs/interconnect/how-to/l2-forwarding/creating-l2-attachments).

        See also: [Interconnect attachments API](https://cloud.google.com/compute/docs/reference/rest/v1/interconnectAttachments).
    """,
}
