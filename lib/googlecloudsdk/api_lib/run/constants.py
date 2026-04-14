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
"""Run constants."""

# Common field names in Cloud Run (K8s-style) resources.
METADATA = 'metadata'
NAMESPACE = 'namespace'
SPEC = 'spec'
TEMPLATE = 'template'
ANNOTATIONS = 'annotations'
STATUS = 'status'
TRAFFIC = 'traffic'
PERCENT = 'percent'
SERVICE_ACCOUNT_NAME = 'serviceAccountName'
REVISION_NAME = 'revisionName'

# Execution environment values.
GEN1 = 'gen1'
GEN2 = 'gen2'

# SSH specific constants.
SSH_ROOT_USER = 'root'
SSH_HOST_KEY_ALIAS = 'cloud-run-default'
SSH_URL_TEMPLATE = 'wss://{region}.ssh.run.app/v4'
SSH_CA_PUBLIC_KEY_URL_TEMPLATE = (
    'https://www.gstatic.com/cloud-run/ssh-ca-public-keys/keys-{region}.pub'
)
