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
"""Flags and helpers for Oracle Connection Profiles related commands."""


def AddDatabaseServiceFlag(parser, required=True):
  """Add the database service field to the parser."""
  parser.add_argument(
      '--database-service',
      required=required,
      help='database service for the oracle connection profile.',
  )


def AddAsmHostFlag(parser):
  """Adds a --asm-host flag to the given parser."""
  help_text = 'Hostname for the Oracle ASM connection.'
  parser.add_argument('--asm-host', help=help_text, required=True)


def AddAsmPortFlag(parser):
  """Adds a --asm-port flag to the given parser."""
  help_text = 'Port for the Oracle ASM connection.'
  parser.add_argument(
      '--asm-port', help=help_text, required=True, type=int
  )


def AddAsmUserFlag(parser):
  """Adds a --asm-user flag to the given parser."""
  help_text = 'Username for the Oracle ASM connection.'
  parser.add_argument('--asm-user', help=help_text, required=True)


def AddAsmPasswordFlag(parser):
  """Adds a --asm-password flag to the given parser."""
  help_text = 'Password for the Oracle ASM connection.'
  parser.add_argument('--asm-password', help=help_text, required=True)


def AddAsmServiceNameFlag(parser):
  """Adds a --asm-service-name flag to the given parser."""
  help_text = 'ASM service name for the Oracle ASM connection.'
  parser.add_argument('--asm-service-name', help=help_text, required=True)


def AddOracleAsmFlags(parser):
  """Adds the Oracle ASM connectivity flags to the given parser."""
  asm_group = parser.add_group(
      help='Oracle Automatic Storage Management (ASM) configuration.',
      required=False,
  )
  AddAsmHostFlag(asm_group)
  AddAsmPortFlag(asm_group)
  AddAsmUserFlag(asm_group)
  AddAsmPasswordFlag(asm_group)
  AddAsmServiceNameFlag(asm_group)

