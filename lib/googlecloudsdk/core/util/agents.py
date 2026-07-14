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
"""Utilities for detecting AI agents in the environment."""

import os

from googlecloudsdk.core.util import encoding

# LINT.IfChange
AI_AGENTS = [
    ('ANTIGRAVITY_AGENT', 'antigravity'),
    ('CLAUDECODE', 'claude_code'),
    ('CLINE_ACTIVE', 'cline'),
    ('CODEX_SANDBOX', 'codex_cli'),
    ('CURSOR_AGENT', 'cursor'),
    ('GEMINI_CLI', 'gemini_cli'),
    ('OPENCODE', 'open_code'),
    ('ANDROID_STUDIO_AGENT', 'android_studio_agent'),
    ('KIRO_AGENT_PATH', 'kiro'),
]
# LINT.ThenChange(../../../../../cloud/helix/clients/cli/bq_utils.py)


def DetectAIAgent():
  """Detects the AI agent based on environment variables.

  Returns:
    str, The name of the AI agent or None.
  """
  for env_var, agent_name in AI_AGENTS:
    if encoding.GetEncodedValue(os.environ, env_var):
      return agent_name
  return None
