#!/usr/bin/env python
"""Utilities to run gcloud for the BQ CLI."""

import logging
import os
import subprocess
from typing import List, Optional

import bq_utils
from pyglib import resources


def _get_gcloud_path() -> str:
  """Returns the string to use to call gcloud."""
  if 'nt' == os.name:
    binary = 'gcloud.cmd'
  else:
    binary = 'gcloud'
  if bq_utils.IS_TPC_BINARY:
    binary = resources.GetResourceFilename('google3/cloud/sdk/gcloud/' + binary)
  logging.info('Found gcloud path: %s', binary)
  return binary


# Before python 3.09 the return type `subprocess.Popen[str]` is unsupported.
def run_gcloud_command(
    cmd: List[str], stderr: Optional[int] = None
) -> subprocess.Popen:  # pylint: disable=g-bare-generic
  """Runs the given gcloud command and returns the Popen object."""
  return subprocess.Popen(
      [_get_gcloud_path()] + cmd,
      stdout=subprocess.PIPE,
      stderr=stderr,
      universal_newlines=True,
  )
