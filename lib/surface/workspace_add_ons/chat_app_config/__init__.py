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

"""The command group for Google Chat app configurations."""


from googlecloudsdk.calliope import base


# Hidden until the chat-app-config beta launch (go/gcp-cli-for-chatappconfig).
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class ChatAppConfig(base.Group):
  """Manage the Google Chat app configuration of a project.

  Commands for viewing and updating the configuration of the Google Chat app
  that belongs to a Google Cloud project. A project has at most one Chat app
  configuration.

  For more information about Chat apps and their configuration, see
  https://developers.google.com/workspace/chat/overview.
  """
