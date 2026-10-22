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
"""Flags for the Serverless Orchestration deploy and trigger flows.

The `deploy` and `trigger` commands do not call these yet: adding flags
changes their help text, which is owned together with the surface. Until then
the flows only read the flags the commands already have (`--environment`,
`--pipeline`, `--runner`, `--async`, `--substitutions`, `--project`).
"""

import argparse


def AddDeployFlags(parser: argparse.ArgumentParser) -> None:
  """Adds the Serverless Orchestration specific `deploy` flags.

  Args:
    parser: The argparse parser of the `deploy` command.
  """
  # TODO(b/567520802): Add --pipeline-file, --region, --service-account,
  # --artifact-bucket and --version-id. A no-op until then: `Args` runs when
  # the command loads, so this must not raise.
  del parser


def AddTriggerFlags(parser: argparse.ArgumentParser) -> None:
  """Adds the Serverless Orchestration specific `trigger` flags.

  Args:
    parser: The argparse parser of the `trigger` command.
  """
  # TODO(b/567520802): Add --region, --run-id and --variables. A no-op until
  # then: `Args` runs when the command loads, so this must not raise.
  del parser
