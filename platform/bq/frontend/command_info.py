#!/usr/bin/env python
"""The BQ CLI `info` command."""

import bq_utils
from frontend import bigquery_command


class Info(bigquery_command.BigqueryCmd):
  usage = """info"""

  def _NeedsInit(self) -> bool:
    """If just printing known versions, don't run `init` first."""
    return False

  def RunWithArgs(self) -> None:
    """Return the execution information of bq."""
    print(bq_utils.GetInfoString())
