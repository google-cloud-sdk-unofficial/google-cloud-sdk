# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Constants for interacting with the Cloud NetApp Files API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


API_NAME = 'netapp'
ALPHA_API_VERSION = 'v1alpha1'

VOLUMES_COLLECTION = 'netapp.projects.locations.volumes'
STORAGEPOOLS_COLLECTION = 'netapp.projects.locations.storagePools'
ACTIVEDIRECTORIES_COLLECTION = 'netapp.projects.locations.activeDirectories'
SNAPSHOTS_COLLECTION = 'netapp.projects.locations.volumes.snapshots'
OPERATIONS_COLLECTION = 'netapp.projects.locations.operations'
LOCATIONS_COLLECTION = 'netapp.projects.locations'

ACTIVE_DIRECTORY_RESOURCE = 'activeDirectories'
STORAGE_POOL_RESOURCE = 'storagePools'
VOLUME_RESOURCE = 'volumes'
SNAPSHOT_RESOURCE = 'snapshots'
