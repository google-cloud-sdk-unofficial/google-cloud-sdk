#!/usr/bin/env python
"""API utils for the BQ CLI."""

import enum


class Service(str, enum.Enum):
  """Enum for the different BigQuery APIs supported."""

  ANALYTICS_HUB = 'analyticshub'
  BIGLAKE = 'biglake'
  BIGQUERY = 'bigquery'
  CONNECTIONS = 'bigqueryconnection'
  RESERVATIONS = 'bigqueryreservation'
  DTS = 'bigquerydatatransfer'
  # This is the BQ core discovery doc with some IAM additions. See cl/600781292
  # for exactly what is added. There is some context in b/296612193 but IAM
  # needs to be a separate enum option until Dataset IAM is launched
  # (b/284146366).
  BQ_IAM = 'bigquery'

  # We can't used StrEnum until min python support is version 3.11
  def __str__(self) -> str:
    return self.value
