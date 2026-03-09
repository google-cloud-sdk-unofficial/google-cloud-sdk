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
"""API lib for Gemini Cloud Assist."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base


VERSION_MAP = {
    base.ReleaseTrack.GA: 'v1',
    base.ReleaseTrack.BETA: 'v1beta'
}


def GetMessageName(message_name, release_track):
  """Returns the full message name for the given release track.

  Args:
    message_name: The name of the message (e.g. 'DenseVector' or
      'SearchHint.IndexHint').
    release_track: The release track to use.

  Returns:
    The full message name for the given release track.
  """
  version = VERSION_MAP.get(release_track)
  # Version is like 'v1' or 'v1beta'. We need 'V1' or 'V1beta'.
  version_capitalized = version[0].upper() + version[1:]
  # Handle nested messages which might be represented as 'Outer.Inner'
  # and flattened in apitools as 'OuterInner'.
  clean_message_name = message_name.replace('.', '')
  return f'GoogleCloudVectorsearch{version_capitalized}{clean_message_name}'


def GetMessage(messages, message_name, release_track):
  """Returns the message for the given release track.

  Args:
    messages: The messages module.
    message_name: The name of the message (e.g. 'DenseVector').
    release_track: The release track to use.

  Returns:
    The message for the given release track.
  """
  full_message_name = GetMessageName(message_name, release_track)
  return getattr(messages, full_message_name)


# The messages module can also be accessed from client.MESSAGES_MODULE
def GetMessagesModule(release_track=base.ReleaseTrack.BETA):
  """Returns the messages module for the given release track.

  Args:
    release_track: The release track to use.

  Returns:
    The messages module for the given release track.
  """
  return apis.GetMessagesModule('vectorsearch', VERSION_MAP.get(release_track))


def GetClientInstance(release_track=base.ReleaseTrack.BETA):
  """Returns the client instance for the given release track.

  Args:
    release_track: The release track to use.

  Returns:
    The client instance for the given release track.
  """
  return apis.GetClientInstance('vectorsearch', VERSION_MAP.get(release_track))
