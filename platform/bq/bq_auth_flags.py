#!/usr/bin/env python
"""Auth flags for calling BigQuery."""

import os



from absl import flags


_USE_GCE_SERVICE_ACCOUNT = flags.DEFINE_boolean(
    'use_gce_service_account',
    False,
    'Only for the gcloud wrapper use.'
)
CREDENTIAL_FILE = flags.DEFINE_string(
    'credential_file',
    os.path.join(
        os.path.expanduser('~'),
        '.bigquery.v2.token'
    ),
    'Only for the gcloud wrapper use.'
)
_APPLICATION_DEFAULT_CREDENTIAL_FILE = flags.DEFINE_string(
    'application_default_credential_file',
    '',
    'Only for the gcloud wrapper use.'
)
_SERVICE_ACCOUNT = flags.DEFINE_string(
    'service_account',
    '',
    'Only for the gcloud wrapper use.'
)
_SERVICE_ACCOUNT_PRIVATE_KEY_FILE = flags.DEFINE_string(
    'service_account_private_key_file',
    '',
    'Only for the gcloud wrapper use.'
)
_SERVICE_ACCOUNT_PRIVATE_KEY_PASSWORD = flags.DEFINE_string(
    'service_account_private_key_password',
    'notasecret',
    'Only for the gcloud wrapper use.'
)
_SERVICE_ACCOUNT_CREDENTIAL_FILE = flags.DEFINE_string(
    'service_account_credential_file',
    None,
    'Only for the gcloud wrapper use.'
)
OAUTH_ACCESS_TOKEN = flags.DEFINE_string(
    'oauth_access_token',
    '',
    'Only for the gcloud wrapper use.'
)
USE_GOOGLE_AUTH = flags.DEFINE_boolean(
    'use_google_auth', False, 'Use new google auth libraries'
)
QUOTA_PROJECT_ID = flags.DEFINE_string(
    'quota_project_id',
    '',
    'ID of a Google Cloud Project as the quota project to be used for billing '
    'and quota limits.',
)
