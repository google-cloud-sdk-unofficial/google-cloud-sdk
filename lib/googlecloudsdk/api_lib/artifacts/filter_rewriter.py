# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""Artifact resource filter expression rewrite backend.

Refer to the core.resource.resource_expr_rewrite docstring for expression
rewrite details.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_expr_rewrite


class Rewriter(resource_expr_rewrite.Backend):
  """Artifact resource filter expression rewriter backend.

  Rewriter is used for all artifacts resources List APIs where filtering on
  annotations and name is done only in the server side.
  """

  def Rewrite(self, expression, defaults=None):
    if expression:
      if expression.startswith("annotations") or expression.startswith("name="):
        return None, expression
    return expression, None
