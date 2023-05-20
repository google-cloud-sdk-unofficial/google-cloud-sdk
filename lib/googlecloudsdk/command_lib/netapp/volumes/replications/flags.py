# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the Cloud NetApp Files Volume Replications commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers


## Helper functions to add args / flags for Replications gcloud commands ##
def AddReplicationVolumeArg(parser, reverse_op=False):
  group_help = (
      'The Volume that the Replication is based on'
      if not reverse_op
      else 'The source Volume to reverse the Replication direction of'
  )
  concept_parsers.ConceptParser.ForResource(
      '--volume',
      flags.GetVolumeResourceSpec(positional=False),
      group_help=group_help,
      flag_name_overrides={'location': ''},
  ).AddToParser(parser)
