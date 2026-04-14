# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Common flags for BigLake commands."""

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers


# A resource argument for a BigLake Iceberg/Hive catalog.
# This defines how to parse the project and catalog from the command line.
def GetCatalogResourceSpec(catalog_type='Iceberg'):
  """Gets the resource spec for a BigLake Iceberg/Hive catalog."""
  return concepts.ResourceSpec(
      'biglake.iceberg.v1.restcatalog.v1.projects.catalogs',
      resource_name='catalog',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      catalogsId=concepts.ResourceParameterAttributeConfig(
          'catalog', f'The {catalog_type} Catalog for the resource.'
      ),
  )


def GetNamespaceResourceSpec(
    catalog_type='Iceberg', namespace_type='namespace'
):
  """Gets the resource spec for a BigLake Iceberg/Hive namespace/database."""
  return concepts.ResourceSpec(
      'biglake.iceberg.v1.restcatalog.v1.projects.catalogs.namespaces',
      resource_name=namespace_type,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      catalogsId=concepts.ResourceParameterAttributeConfig(
          'catalog', f'The {catalog_type} Catalog for the resource.'
      ),
      namespacesId=concepts.ResourceParameterAttributeConfig(
          namespace_type,
          f'The {catalog_type} {namespace_type.capitalize()} for the resource.',
      ),
  )


def GetTableResourceSpec(catalog_type='Iceberg', namespace_type='namespace'):
  """Gets the resource spec for a BigLake Iceberg/Hive table."""
  return concepts.ResourceSpec(
      'biglake.iceberg.v1.restcatalog.v1.projects.catalogs.namespaces.tables',
      resource_name='table',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      catalogsId=concepts.ResourceParameterAttributeConfig(
          'catalog', f'The {catalog_type} Catalog for the resource.'
      ),
      namespacesId=concepts.ResourceParameterAttributeConfig(
          namespace_type,
          f'The {catalog_type} {namespace_type.capitalize()} for the resource.',
      ),
      tablesId=concepts.ResourceParameterAttributeConfig(
          'table', f'The {catalog_type} Table for the resource.'
      ),
  )


def AddCatalogResourceArg(
    parser, verb, positional=True, catalog_type='Iceberg'
):
  """Adds a resource argument for a BigLake catalog.

  Args:
    parser: The argparse parser.
    verb: The verb to describe the resource, e.g., "to list catalogs from".
    positional: Whether the argument should be positional or a flag.
    catalog_type: The type of catalog to add the resource argument for.
  """
  concept_parsers.ConceptParser.ForResource(
      'catalog' if positional else '--catalog',
      GetCatalogResourceSpec(),
      f'The {catalog_type} Catalog {verb}.',
      required=True,
  ).AddToParser(parser)


def AddNamespaceResourceArg(
    parser, verb, positional=True, namespace_type='Iceberg'
):
  """Adds a resource argument for a BigLake Hive/Iceberg namespace/database.

  Args:
    parser: The argparse parser.
    verb: The verb to describe the resource, e.g., "to list namespaces from".
    positional: Whether the argument should be positional or a flag.
    namespace_type: The type of namespace/database to add the resource argument
      for.
  """
  if namespace_type == 'Hive':
    resource_spec = GetNamespaceResourceSpec(
        catalog_type='Hive', namespace_type='database'
    )
    positional_argument = 'database' if positional else '--database'
    help_text = f'The {namespace_type} Database {verb}.'
  else:
    resource_spec = GetNamespaceResourceSpec()
    positional_argument = 'namespace' if positional else '--namespace'
    help_text = f'The {namespace_type} Namespace {verb}.'
  concept_parsers.ConceptParser.ForResource(
      positional_argument,
      resource_spec,
      help_text,
      required=True,
  ).AddToParser(parser)


def AddTableResourceArg(
    parser, verb, positional=True, table_type='Iceberg'
):
  """Adds a resource argument for a BigLake Iceberg/Hive table.

  Args:
    parser: The argparse parser.
    verb: The verb to describe the resource, e.g., "to list tables from".
    positional: Whether the argument should be positional or a flag.
    table_type: The type of table to add the resource argument for.
  """
  if table_type == 'Hive':
    resource_spec = GetTableResourceSpec(
        catalog_type='Hive', namespace_type='database'
    )
  else:
    resource_spec = GetTableResourceSpec()

  concept_parsers.ConceptParser.ForResource(
      'table' if positional else '--table',
      resource_spec,
      f'The {table_type} Table {verb}.',
      required=True,
  ).AddToParser(parser)
