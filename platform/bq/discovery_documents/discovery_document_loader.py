#!/usr/bin/env python
"""Methods for loading discovery documents for Google Cloud APIs.

Discovery Documents are used to create API Clients.
"""

import pkgutil
from typing import Optional
from absl import logging

PKG_NAME = 'bigquery_client'

# Latest version of the BigQuery API discovery_document from discovery_next.
DISCOVERY_NEXT_BIGQUERY = 'discovery_next/bigquery.json'
# Latest version of the IAM Policy API discovery_document from discovery_next.
DISCOVERY_NEXT_IAM_POLICY = 'discovery_next/iam-policy.json'

SUPPORTED_BIGQUERY_APIS = frozenset([
    'https://www.googleapis.com',
    'https://bigquery.googleapis.com',
])


def load_local_discovery_doc(doc_filename: str) -> bytes:
  """Loads the discovery document for `doc_filename` with `version` from package files.

  Example:
    bq_disc_doc = discovery_document_loader
      .load_local_discovery_doc('discovery_next/bigquery.json')

  Args:
    doc_filename: [str], The filename of the discovery document to be loaded.

  Raises:
    FileNotFoundError: If no discovery doc could be loaded.

  Returns:
    `bytes`, On success, A json object with the contents of the
    discovery document. On failure, None.
  """
  doc = _fetch_discovery_doc_from_pkg(PKG_NAME, doc_filename)

  if not doc:
    raise FileNotFoundError(
        'Failed to load discovery doc from resource path: %s.%s' %
        (PKG_NAME, doc_filename))

  return doc


def _fetch_discovery_doc_from_pkg(
    package: str, resource: str
) -> Optional[bytes]:
  """Loads a discovery doc as `bytes` specified by `package` and `resource` returning None on error."""
  try:
    raw_doc = pkgutil.get_data(package, resource)
  # TODO(b/286571605) Ideally this would be ModuleNotFoundError but it's not
  # supported before python3.6 so we need to be less specific for now.
  except ImportError:
    raw_doc = None
  if not raw_doc:
    logging.warning(
        'Failed to load discovery doc from (package, resource): %s, %s',
        package, resource)
  else:
    logging.info(
        'Successfully loaded discovery doc from (package, resource): %s, %s',
        package, resource)
  return raw_doc
