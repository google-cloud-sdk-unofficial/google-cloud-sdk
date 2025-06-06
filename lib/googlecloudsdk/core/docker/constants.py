# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Default value constants exposed by core utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


DEFAULT_REGISTRY = 'gcr.io'
REGIONAL_GCR_REGISTRIES = ['us.gcr.io', 'eu.gcr.io', 'asia.gcr.io']
REGIONAL_AR_REGISTRIES = [
    'africa-south1-docker.pkg.dev',
    'docker.africa-south1.rep.pkg.dev',
    'asia-docker.pkg.dev',
    'asia-east1-docker.pkg.dev',
    'docker.asia-east1.rep.pkg.dev',
    'asia-east2-docker.pkg.dev',
    'docker.asia-east2.rep.pkg.dev',
    'asia-northeast1-docker.pkg.dev',
    'docker.asia-northeast1.rep.pkg.dev',
    'asia-northeast2-docker.pkg.dev',
    'docker.asia-northeast2.rep.pkg.dev',
    'asia-northeast3-docker.pkg.dev',
    'docker.asia-northeast3.rep.pkg.dev',
    'asia-south1-docker.pkg.dev',
    'docker.asia-south1.rep.pkg.dev',
    'asia-south2-docker.pkg.dev',
    'docker.asia-south2.rep.pkg.dev',
    'asia-southeast1-docker.pkg.dev',
    'docker.asia-southeast1.rep.pkg.dev',
    'asia-southeast2-docker.pkg.dev',
    'docker.asia-southeast2.rep.pkg.dev',
    'australia-southeast1-docker.pkg.dev',
    'docker.australia-southeast1.rep.pkg.dev',
    'australia-southeast2-docker.pkg.dev',
    'docker.australia-southeast2.rep.pkg.dev',
    'europe-docker.pkg.dev',
    'europe-central2-docker.pkg.dev',
    'docker.europe-central2.rep.pkg.dev',
    'europe-north1-docker.pkg.dev',
    'docker.europe-north1.rep.pkg.dev',
    'europe-north2-docker.pkg.dev',
    'europe-southwest1-docker.pkg.dev',
    'docker.europe-southwest1.rep.pkg.dev',
    'europe-west1-docker.pkg.dev',
    'docker.europe-west1.rep.pkg.dev',
    'europe-west10-docker.pkg.dev',
    'docker.europe-west10.rep.pkg.dev',
    'europe-west12-docker.pkg.dev',
    'docker.europe-west12.rep.pkg.dev',
    'europe-west2-docker.pkg.dev',
    'docker.europe-west2.rep.pkg.dev',
    'europe-west3-docker.pkg.dev',
    'docker.europe-west3.rep.pkg.dev',
    'europe-west4-docker.pkg.dev',
    'docker.europe-west4.rep.pkg.dev',
    'europe-west6-docker.pkg.dev',
    'docker.europe-west6.rep.pkg.dev',
    'europe-west8-docker.pkg.dev',
    'docker.europe-west8.rep.pkg.dev',
    'europe-west9-docker.pkg.dev',
    'docker.europe-west9.rep.pkg.dev',
    'me-central1-docker.pkg.dev',
    'docker.me-central1.rep.pkg.dev',
    'me-central2-docker.pkg.dev',
    'docker.me-central2.rep.pkg.dev',
    'me-west1-docker.pkg.dev',
    'docker.me-west1.rep.pkg.dev',
    'northamerica-northeast1-docker.pkg.dev',
    'docker.northamerica-northeast1.rep.pkg.dev',
    'northamerica-northeast2-docker.pkg.dev',
    'docker.northamerica-northeast2.rep.pkg.dev',
    'northamerica-south1-docker.pkg.dev',
    'southamerica-east1-docker.pkg.dev',
    'docker.southamerica-east1.rep.pkg.dev',
    'southamerica-west1-docker.pkg.dev',
    'docker.southamerica-west1.rep.pkg.dev',
    'us-docker.pkg.dev',
    'us-central1-docker.pkg.dev',
    'docker.us-central1.rep.pkg.dev',
    'us-central2-docker.pkg.dev',
    'docker.us-central2.rep.pkg.dev',
    'us-east1-docker.pkg.dev',
    'docker.us-east1.rep.pkg.dev',
    'us-east4-docker.pkg.dev',
    'docker.us-east4.rep.pkg.dev',
    'us-east5-docker.pkg.dev',
    'docker.us-east5.rep.pkg.dev',
    'us-east7-docker.pkg.dev',
    'docker.us-east7.rep.pkg.dev',
    'us-south1-docker.pkg.dev',
    'docker.us-south1.rep.pkg.dev',
    'us-west1-docker.pkg.dev',
    'docker.us-west1.rep.pkg.dev',
    'us-west2-docker.pkg.dev',
    'docker.us-west2.rep.pkg.dev',
    'us-west3-docker.pkg.dev',
    'docker.us-west3.rep.pkg.dev',
    'us-west4-docker.pkg.dev',
    'docker.us-west4.rep.pkg.dev',
    'us-west8-docker.pkg.dev',
]
AUTHENTICATED_LAUNCHER_REGISTRIES = ['marketplace.gcr.io']
LAUNCHER_REGISTRIES = AUTHENTICATED_LAUNCHER_REGISTRIES + [
    'l.gcr.io', 'launcher.gcr.io'
]
LAUNCHER_PROJECT = 'cloud-marketplace'
KUBERNETES_PUSH = 'staging-k8s.gcr.io'
KUBERNETES_READ_ONLY = 'k8s.gcr.io'
# GCR's regional demand-based mirrors of DockerHub.
# These are intended for use with the daemon flag, e.g.
#  --registry-mirror=https://mirror.gcr.io
MIRROR_REGISTRIES = [
    'us-mirror.gcr.io', 'eu-mirror.gcr.io', 'asia-mirror.gcr.io',
    'mirror.gcr.io'
]
MIRROR_PROJECT = 'cloud-containers-mirror'
# These are the registries to authenticatefor by default, during
# `gcloud docker` and `gcloud auth configure-docker`
DEFAULT_REGISTRIES_TO_AUTHENTICATE = ([DEFAULT_REGISTRY] +
                                      REGIONAL_GCR_REGISTRIES +
                                      [KUBERNETES_PUSH] +
                                      AUTHENTICATED_LAUNCHER_REGISTRIES)
ALL_SUPPORTED_REGISTRIES = (
    DEFAULT_REGISTRIES_TO_AUTHENTICATE + REGIONAL_AR_REGISTRIES +
    LAUNCHER_REGISTRIES + MIRROR_REGISTRIES + [KUBERNETES_READ_ONLY])
DEFAULT_DEVSHELL_IMAGE = (DEFAULT_REGISTRY + '/dev_con/cloud-dev-common:prod')
METADATA_IMAGE = DEFAULT_REGISTRY + '/google_appengine/faux-metadata:latest'
