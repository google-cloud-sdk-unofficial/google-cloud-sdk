# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the Assured related commands."""


from googlecloudsdk.calliope.concepts import concepts


def OrganizationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='organization',
      help_text='The parent organization for the {resource}.')


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location', help_text='The location for the {resource}.')


def WorkloadAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='workload', help_text='The workload for the {resource}.')


def ViolationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='violation', help_text='The violation for the {resource}.')


def OperationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='operation', help_text='The operation for the {resource}.')


def GetWorkloadResourceSpec():
  return concepts.ResourceSpec(
      'assuredworkloads.organizations.locations.workloads',
      resource_name='workload',
      workloadsId=WorkloadAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      organizationsId=OrganizationAttributeConfig())


def GetViolationResourceSpec():
  return concepts.ResourceSpec(
      'assuredworkloads.organizations.locations.workloads.violations',
      resource_name='violation',
      violationsId=ViolationAttributeConfig(),
      workloadsId=WorkloadAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      organizationsId=OrganizationAttributeConfig())


def GetOperationResourceSpec():
  return concepts.ResourceSpec(
      'assuredworkloads.organizations.locations.operations',
      resource_name='operation',
      operationsId=OperationAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      organizationsId=OrganizationAttributeConfig())


def ComplianceReportAttributeConfig():
  """Returns the attribute config for a framework compliance report."""
  return concepts.ResourceParameterAttributeConfig(
      name='compliance-report',
      help_text=(
          'The Data Boundary framework compliance report for the {resource}.'
      ),
  )


def GetDataBoundaryLocationResourceSpec():
  """Data Boundary location under an organization."""
  # Folder and project scopes will be added once the API supports them.
  return concepts.ResourceSpec(
      'assuredworkloads.organizations.locations',
      resource_name='location',
      locationsId=LocationAttributeConfig(),
      organizationsId=OrganizationAttributeConfig(),
      disable_auto_completers=True,
  )


def GetComplianceReportResourceSpec():
  """Data Boundary framework compliance report under an organization."""
  return concepts.ResourceSpec(
      'assuredworkloads.organizations.locations.dbFrameworkComplianceReports',
      resource_name='compliance report',
      dbFrameworkComplianceReportsId=ComplianceReportAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      organizationsId=OrganizationAttributeConfig(),
      disable_auto_completers=True,
  )
