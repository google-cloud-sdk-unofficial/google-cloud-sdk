# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""The command group for cloud builds."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import transforms
from googlecloudsdk.calliope import base

DEPRECATED_WARNING_MESSAGE = """\
This command is deprecated and will be removed on or after 2018-10-31. Please
use `gcloud builds` instead."""


@base.Deprecate(is_removed=False, warning=DEPRECATED_WARNING_MESSAGE)
class Builds(base.Group):
  """Create and manage builds."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddTransforms(transforms.GetTransforms())
