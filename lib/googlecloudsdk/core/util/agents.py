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

AI_AGENTS = [
    # If the optional asserted value is not set, any value matches.
    # If the optional hardcoded result is set, we use the hardcoded result.
    #   Else, the env var value is used as the result.
    # ENV_VAR, OPTIONAL_ASSERTED_VALUE, OPTIONAL_HARDCODED_RESULT
    ('AI_AGENT', None, None),  # Keep first.
    ('ANTIGRAVITY_AGENT', None, 'antigravity'),
    ('CLAUDECODE', None, 'claude_code'),
    ('CLAUDE_CODE', None, 'claude_code'),
    ('CLINE_ACTIVE', None, 'cline'),
    ('CODEX_SANDBOX', None, 'codex_cli'),
    ('CODEX_CI', None, 'codex_cli'),
    ('CODEX_THREAD_ID', None, 'codex_cli'),
    ('CURSOR_AGENT', None, 'cursor'),
    ('CURSOR_TRACE_ID', None, 'cursor'),
    ('CURSOR_EXTENSION_HOST_ROLE', 'agent-exec', 'cursor'),
    ('GEMINI_CLI', None, 'gemini_cli'),
    ('OPENCODE', None, 'open_code'),
    ('OPENCODE_CLIENT', None, 'open_code'),
    ('ANDROID_STUDIO_AGENT', None, 'android_studio_agent'),
    ('KIRO_AGENT_PATH', None, 'kiro'),
    ('COPILOT_MODEL', None, 'github_copilot'),
    ('COPILOT_ALLOW_ALL', None, 'github_copilot'),
    ('COPILOT_GITHUB_TOKEN', None, 'github_copilot'),
    ('REPL_ID', None, 'replit'),
    ('AUGMENT_AGENT', None, 'augment'),
]


def DetectAIAgent():
  """Detects the AI agent based on environment variables.

  Mirrors https://github.com/firebase/firebase-tools/blob/main/src/env.ts

  Returns:
    str, The name of the AI agent or None.
  """
  for env_var, asserted_value, hardcoded_result in AI_AGENTS:
    val = encoding.GetEncodedValue(os.environ, env_var)
    if val is None:  # Environment variable is not set.
      continue
    val = val.strip()
    if asserted_value and val != asserted_value:
      continue
    if hardcoded_result:
      return hardcoded_result
    if val:
      return val

  return None
