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
"""Base class for Anthos GKE On-Prem API client resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis


# pylint: disable=invalid-name
class ClientBase(object):
  """Base class for Anthos GKE On-Prem API clients."""

  def __init__(self, service=None):
    self._client = apis.GetClientInstance('gkeonprem', 'v1')
    self._messages = self._client.MESSAGES_MODULE
    self._service = service

  def Describe(self, resource_ref):
    """Gets a gkeonprem API resource."""
    req = self._service.GetRequestType('Get')(name=resource_ref.RelativeName())
    return self._service.Get(req)

  def _user_cluster_ref(self, args):
    """Parses user cluster resource argument and returns its reference."""
    if getattr(args.CONCEPTS, 'cluster', None):
      return args.CONCEPTS.cluster.Parse()
    return None

  def _admin_cluster_ref(self, args):
    """Parses admin cluster resource argument and returns its reference."""
    if getattr(args.CONCEPTS, 'admin_cluster', None):
      return args.CONCEPTS.admin_cluster.Parse()
    return None

  def _location_ref(self, args):
    """Parses location resource argument and returns its reference."""
    if getattr(args.CONCEPTS, 'location', None):
      return args.CONCEPTS.location.Parse()
    return None

  def _user_cluster_name(self, args):
    """Parses user cluster from args and returns its name."""
    user_cluster_ref = self._user_cluster_ref(args)
    if user_cluster_ref:
      return user_cluster_ref.RelativeName()
    return None

  def _user_cluster_parent(self, args):
    """Parses user cluster from args and returns its parent name."""
    user_cluster_ref = self._user_cluster_ref(args)
    if user_cluster_ref:
      return user_cluster_ref.Parent().RelativeName()
    return None

  def _user_cluster_id(self, args):
    """Parses user cluster from args and returns its ID."""
    user_cluster_ref = self._user_cluster_ref(args)
    if user_cluster_ref:
      return user_cluster_ref.Name()
    return None

  def _admin_cluster_name(self, args):
    """Parses admin cluster from args and returns its name."""
    admin_cluster_ref = self._admin_cluster_ref(args)
    if admin_cluster_ref:
      return admin_cluster_ref.RelativeName()
    return None

  def _admin_cluster_parent(self, args):
    """Parses admin cluster from args and returns its parent name."""
    admin_cluster_ref = self._admin_cluster_ref(args)
    if admin_cluster_ref:
      return admin_cluster_ref.Parent().RelativeName()
    return None

  def _admin_cluster_id(self, args):
    """Parses admin cluster from args and returns its ID."""
    admin_cluster_ref = self._admin_cluster_ref(args)
    if admin_cluster_ref:
      return admin_cluster_ref.Name()
    return None

  def _admin_cluster_membership_ref(self, args):
    """Parses admin cluster resource argument and returns its reference."""
    if getattr(args.CONCEPTS, 'admin_cluster_membership', None):
      return args.CONCEPTS.admin_cluster_membership.Parse()
    return None

  def _admin_cluster_membership_name(self, args):
    """Parses admin cluster from args and returns its name."""
    admin_cluster_ref = self._admin_cluster_membership_ref(args)
    if admin_cluster_ref:
      return admin_cluster_ref.RelativeName()
    return None

  def _node_pool_ref(self, args):
    """Parses node pool resource argument and returns its reference."""
    if getattr(args.CONCEPTS, 'node_pool', None):
      return args.CONCEPTS.node_pool.Parse()
    return None

  def _node_pool_name(self, args):
    """Parses node pool from args and returns its name."""
    node_pool_ref = self._node_pool_ref(args)
    if node_pool_ref:
      return node_pool_ref.RelativeName()
    return None

  def _node_pool_id(self, args):
    """Parses node pool from args and returns its ID."""
    node_pool_ref = self._node_pool_ref(args)
    if node_pool_ref:
      return node_pool_ref.Name()
