# -*- coding: utf-8 -*- # Lint as: python3
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
"""The deployments command group for the Apigee CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Deployments(base.Group):
  """Manage deployments of Apigee proxies in runtime environments."""

  detailed_help = {
      "DESCRIPTION": """
          {description}

          Commands to list deployments are available in the command groups of
          the desired search terms. For example, to list all deployments to an
          environment, use `{parent_command} environments deployments list`
          instead of this command group.
          """
  }
