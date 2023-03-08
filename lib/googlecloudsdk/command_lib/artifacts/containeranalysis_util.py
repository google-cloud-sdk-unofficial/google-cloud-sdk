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
"""Utility for interacting with containeranalysis API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.containeranalysis import filter_util
from googlecloudsdk.api_lib.containeranalysis import requests as ca_requests
import six


class ContainerAnalysisMetadata:
  """ContainerAnalysisMetadata defines metadata retrieved from containeranalysis API."""

  def __init__(self):
    self.vulnerability = PackageVulnerabilitySummary()
    self.image = ImageBasisSummary()
    self.discovery = DiscoverySummary()
    self.deployment = DeploymentSummary()
    self.build = BuildSummary()
    self.provenance = ProvenanceSummary()
    self.package = PackageSummary()
    self.attestation = AttestationSummary()
    self.upgrade = UpgradeSummary()
    self.compliance = ComplianceSummary()
    self.dsse_attestation = DsseAttestaionSummary()

  def AddOccurrence(self, occ, include_build=True):
    """Adds occurrences retrieved from containeranalysis API.

    Generally we have a 1-1 correspondence between type and summary it's added
    to. The exceptions (due to backwards compatibility issues) are:
    BUILD: If you pass in --show-provenance, there will be a provenance
    section (for intoto builds) but no build section. If you pass in
    --show-all-metadata or --show-build-details, there will be a provenance
    section (for intoto builds) and a builds section (for every build). That
    does mean an occurrence may be in both provenance_summary and build_summary.
    DSSE_ATTESTATION: We always return it in both the DSSE_ATTESTATION section
    and the provenance section.

    Args:
      occ: the occurrence retrieved from the API.
      include_build: whether build-kind occurrences should be added to build.
    """
    messages = ca_requests.GetMessages()
    if occ.kind == messages.Occurrence.KindValueValuesEnum.VULNERABILITY:
      self.vulnerability.AddOccurrence(occ)
    elif occ.kind == messages.Occurrence.KindValueValuesEnum.IMAGE:
      self.image.AddOccurrence(occ)
    elif occ.kind == messages.Occurrence.KindValueValuesEnum.DEPLOYMENT:
      self.deployment.AddOccurrence(occ)
    elif occ.kind == messages.Occurrence.KindValueValuesEnum.DISCOVERY:
      self.discovery.AddOccurrence(occ)
    elif occ.kind == messages.Occurrence.KindValueValuesEnum.DSSE_ATTESTATION:
      self.provenance.AddOccurrence(occ)
    elif occ.kind == messages.Occurrence.KindValueValuesEnum.BUILD and occ.build and occ.build.intotoStatement:
      self.provenance.AddOccurrence(occ)
    elif occ.kind == messages.Occurrence.KindValueValuesEnum.PACKAGE:
      self.package.AddOccurrence(occ)
    elif occ.kind == messages.Occurrence.KindValueValuesEnum.ATTESTATION:
      self.attestation.AddOccurrence(occ)
    elif occ.kind == messages.Occurrence.KindValueValuesEnum.UPGRADE:
      self.upgrade.AddOccurrence(occ)
    elif occ.kind == messages.Occurrence.KindValueValuesEnum.COMPLIANCE:
      self.compliance.AddOccurrence(occ)
    # DSSEAttestation should also have its own section, even if it was already
    # added to the provenance section, as a user can make a non-provenance dsse.
    if occ.kind == messages.Occurrence.KindValueValuesEnum.DSSE_ATTESTATION:
      self.dsse_attestation.AddOccurrence(occ)
    # BUILD should also have its own section, even if it was already
    # added to the provenance section.
    if occ.kind == messages.Occurrence.KindValueValuesEnum.BUILD and include_build:
      self.build.AddOccurrence(occ)

  def ImagesListView(self):
    """Returns a dictionary representing the metadata.

    The returned dictionary is used by artifacts docker images list command.
    """
    view = {}
    if self.image.base_images:
      view['IMAGE'] = self.image.base_images
    if self.deployment.deployments:
      view['DEPLOYMENT'] = self.deployment.deployments
    if self.discovery.discovery:
      view['DISCOVERY'] = self.discovery.discovery
    if self.build.build_details:
      view['BUILD'] = self.build.build_details
    if self.package.packages:
      view['PACKAGE'] = self.package.packages
    if self.attestation.attestations:
      view['ATTESTATION'] = self.attestation.attestations
    if self.upgrade.upgrades:
      view['UPGRADE'] = self.upgrade.upgrades
    if self.compliance.compliances:
      view['COMPLIANCE'] = self.compliance.compliances
    if self.dsse_attestation.dsse_attestations:
      view['DSSE_ATTESTATION'] = self.dsse_attestation.dsse_attestations
    view.update(self.vulnerability.ImagesListView())
    return view

  def ArtifactsDescribeView(self):
    """Returns a dictionary representing the metadata.

    The returned dictionary is used by artifacts docker images describe command.
    """
    view = {}
    if self.image.base_images:
      view['image_basis_summary'] = self.image
    if self.deployment.deployments:
      view['deployment_summary'] = self.deployment
    if self.discovery.discovery:
      view['discovery_summary'] = self.discovery
    if self.build.build_details:
      view['build_details_summary'] = self.build
    vuln = self.vulnerability.ArtifactsDescribeView()
    if vuln:
      view['package_vulnerability_summary'] = vuln
    if self.provenance.provenance:
      view['provenance_summary'] = self.provenance
    if self.package.packages:
      view['package_summary'] = self.package
    if self.attestation.attestations:
      view['attestation_summary'] = self.attestation
    if self.upgrade.upgrades:
      view['upgrade_summary'] = self.upgrade
    if self.compliance.compliances:
      view['compliance_summary'] = self.compliance
    if self.dsse_attestation.dsse_attestations:
      view['dsse_attestation_summary'] = self.dsse_attestation
    return view


class PackageVulnerabilitySummary:
  """PackageVulnerabilitySummary holds package vulnerability information."""

  def __init__(self):
    self.vulnerabilities = {}
    self.counts = []

  def AddOccurrence(self, occ):
    sev = six.text_type(occ.vulnerability.effectiveSeverity)
    self.vulnerabilities.setdefault(sev, []).append(occ)

  def AddSummary(self, summary):
    self.counts += summary.counts

  def AddCount(self, count):
    self.counts.append(count)

  def ArtifactsDescribeView(self):
    """Returns a dictionary representing package vulnerability metadata.

    The returned dictionary is used by artifacts docker images describe command.
    """
    messages = ca_requests.GetMessages()
    view = {}
    if self.vulnerabilities:
      view['vulnerabilities'] = self.vulnerabilities
    for count in self.counts:
      # SEVERITY_UNSPECIFIED represents total counts across all serverities
      if (count.severity == messages.FixableTotalByDigest
          .SeverityValueValuesEnum.SEVERITY_UNSPECIFIED):
        view['not_fixed_vulnerability_count'] = (
            count.totalCount - count.fixableCount)
        view['total_vulnerability_count'] = count.totalCount
        break
    return view

  def ImagesListView(self):
    """Returns a dictionary representing package vulnerability metadata.

    The returned dictionary is used by artifacts docker images list command.
    """
    messages = ca_requests.GetMessages()
    view = {}
    if self.vulnerabilities:
      view['PACKAGE_VULNERABILITY'] = self.vulnerabilities
    vuln_counts = {}
    for count in self.counts:
      # SEVERITY_UNSPECIFIED represents total counts across all serverities
      sev = count.severity
      if (sev and sev != messages.FixableTotalByDigest.SeverityValueValuesEnum
          .SEVERITY_UNSPECIFIED):
        vuln_counts.update({sev: vuln_counts.get(sev, 0) + count.totalCount})
    if vuln_counts:
      view['vuln_counts'] = vuln_counts
    return view


class ImageBasisSummary:
  """ImageBasisSummary holds image basis information."""

  def __init__(self):
    self.base_images = []

  def AddOccurrence(self, occ):
    self.base_images.append(occ)


class BuildSummary:
  """BuildSummary holds image build information."""

  def __init__(self):
    self.build_details = []

  def AddOccurrence(self, occ):
    self.build_details.append(occ)


class DeploymentSummary:
  """DeploymentSummary holds image deployment information."""

  def __init__(self):
    self.deployments = []

  def AddOccurrence(self, occ):
    self.deployments.append(occ)


class DiscoverySummary:
  """DiscoverySummary holds image vulnerability discovery information."""

  def __init__(self):
    self.discovery = []

  def AddOccurrence(self, occ):
    self.discovery.append(occ)


class ProvenanceSummary:
  """ProvenanceSummary holds image provenance information."""

  def __init__(self):
    self.provenance = []

  def AddOccurrence(self, occ):
    self.provenance.append(occ)


class PackageSummary:
  """PackageSummary holds image package information."""

  def __init__(self):
    self.packages = []

  def AddOccurrence(self, occ):
    self.packages.append(occ)


class AttestationSummary:
  """AttestationSummary holds image attestation information."""

  def __init__(self):
    self.attestations = []

  def AddOccurrence(self, occ):
    self.attestations.append(occ)


class UpgradeSummary:
  """UpgradeSummary holds image upgrade information."""

  def __init__(self):
    self.upgrades = []

  def AddOccurrence(self, occ):
    self.upgrades.append(occ)


class ComplianceSummary:
  """ComplianceSummary holds image compliance information."""

  def __init__(self):
    self.compliances = []

  def AddOccurrence(self, occ):
    self.compliances.append(occ)


class DsseAttestaionSummary:
  """DsseAttestaionSummary holds image dsse_attestation information."""

  def __init__(self):
    self.dsse_attestations = []

  def AddOccurrence(self, occ):
    self.dsse_attestations.append(occ)


def GetContainerAnalysisMetadata(docker_version, args):
  """Retrieves metadata for a docker image."""
  metadata = ContainerAnalysisMetadata()
  docker_urls = [
      'https://{}'.format(docker_version.GetDockerString()),
      docker_version.GetDockerString()
  ]
  occ_filter = _CreateFilterFromImagesDescribeArgs(docker_urls, args)
  if occ_filter is None:
    return metadata
  occurrences = ca_requests.ListOccurrences(docker_version.project, occ_filter)
  include_build = args.show_build_details or args.show_all_metadata
  for occ in occurrences:
    metadata.AddOccurrence(occ, include_build)

  if metadata.vulnerability.vulnerabilities:
    vuln_summary = ca_requests.GetVulnerabilitySummary(
        docker_version.project,
        filter_util.ContainerAnalysisFilter().WithResources(docker_urls)
        .GetFilter())
    metadata.vulnerability.AddSummary(vuln_summary)
  return metadata


def GetMavenArtifactOccurrences(project, maven_resource):
  """Retrieves occurrences for Maven artifacts."""
  metadata = ContainerAnalysisMetadata()

  occ_filter = _CreateFilterForMaven(maven_resource)

  occurrences = ca_requests.ListOccurrences(project, occ_filter)
  for occ in occurrences:
    metadata.AddOccurrence(occ, False)

  return metadata


def GetContainerAnalysisMetadataForImages(repo_or_image, occurrence_filter,
                                          images):
  """Retrieves metadata for all images with a given path prefix.

  The prefix may initially be used to resolve to a list of images if
  --show-occurrences-from is used.
  To account for cases where there is or isn't a list of images,
  this always filters on both prefix and the list of images. In both of
  those cases, the lookup is for both the case where there is and isn't
  an https prefix, in both the prefixes and in the images list.

  Args:
    repo_or_image: The repository originally given by the user.
    occurrence_filter: The repository originally given by the user.
    images: The list of images that matched the prefix, without https prepended.

  Returns:
    The metadata about the given images.
  """
  metadata = collections.defaultdict(ContainerAnalysisMetadata)
  prefixes = ['https://{}'.format(repo_or_image.GetDockerString()),
              repo_or_image.GetDockerString()]
  image_urls = images + ['https://{}'.format(img) for img in images]
  occ_filters = _CreateFilterForImages(prefixes, occurrence_filter, image_urls)
  occurrences = ca_requests.ListOccurrencesWithFilters(repo_or_image.project,
                                                       occ_filters)
  for occ in occurrences:
    metadata.setdefault(occ.resourceUri,
                        ContainerAnalysisMetadata()).AddOccurrence(occ)

  summary_filters = filter_util.ContainerAnalysisFilter().WithResourcePrefixes(
      prefixes).WithResources(image_urls).GetChunkifiedFilters()
  summaries = ca_requests.GetVulnerabilitySummaryWithFilters(
      repo_or_image.project, summary_filters)
  for summary in summaries:
    for count in summary.counts:
      metadata.setdefault(
          count.resourceUri,
          ContainerAnalysisMetadata()).vulnerability.AddCount(count)

  return metadata


def _CreateFilterForMaven(maven_resource):
  """Builds filters for containeranalysis APIs for Maven Artifacts."""
  occ_filter = filter_util.ContainerAnalysisFilter()

  filter_kinds = ['VULNERABILITY', 'DISCOVERY']

  occ_filter.WithKinds(filter_kinds)
  occ_filter.WithResources([maven_resource])
  return occ_filter.GetFilter()


def _CreateFilterFromImagesDescribeArgs(images, args):
  r"""Parses `docker images describe` arguments into a filter to send to containeranalysis API.

  The returned filter will combine the user-provided filter specified by
  the --metadata-filter flag and occurrence kind filters specified by flags
  such as --show-package-vulnerability.

  Returns None if there is no information to fetch from containeranalysis API.

  Args:
    images: list, the fully-qualified path of docker images.
    args: user provided command line arguments.

  Returns:
    A filter string to send to the containeranalysis API.

  For example, given a user input:
  gcloud docker images describe \
    us-west1-docker.pkg.dev/my-project/my-repo/ubuntu@sha256:abc \
    --show-package-vulnerability \
    --show-image-basis \
    --metadata-filter='createTime>"2019-04-10T"'

  this method will create a filter:

  '''
  ((kind="VULNERABILITY") OR (kind="IMAGE")) AND
  (createTime>"2019-04-10T") AND
  (resourceUrl=us-west1-docker.pkg.dev/my-project/my-repo/ubuntu@sha256:abc' OR
  resourceUrl=https://us-west1-docker.pkg.dev/my-project/my-repo/ubuntu@sha256:abc'))
  '''
  """

  occ_filter = filter_util.ContainerAnalysisFilter()
  filter_kinds = []
  # We don't need to filter on kinds when showing all metadata
  if not args.show_all_metadata:
    if args.show_build_details:
      filter_kinds.append('BUILD')
    if args.show_package_vulnerability:
      filter_kinds.append('VULNERABILITY')
      filter_kinds.append('DISCOVERY')
    if args.show_image_basis:
      filter_kinds.append('IMAGE')
    if args.show_deployment:
      filter_kinds.append('DEPLOYMENT')
    if args.show_provenance:
      filter_kinds.append('DSSE_ATTESTATION')
      filter_kinds.append('BUILD')

    # args include none of the occurrence types, there's no need to call the
    # containeranalysis API.
    if not filter_kinds:
      return None

  occ_filter.WithKinds(filter_kinds)
  occ_filter.WithCustomFilter(args.metadata_filter)
  occ_filter.WithResources(images)
  return occ_filter.GetFilter()


def _CreateFilterForImages(prefixes, custom_filter, images):
  """Creates a list of filters from a docker image prefix, a custom filter and fully-qualified image URLs.

  Args:
    prefixes: URL prefixes. Only metadata of images with any of these
    prefixes will be retrieved.
    custom_filter: user provided filter string.
    images: fully-qualified docker image URLs. Only metadata of these images
      will be retrieved.

  Returns:
    A filter string to send to the containeranalysis API.
  """
  occ_filter = filter_util.ContainerAnalysisFilter()
  occ_filter.WithResourcePrefixes(prefixes)
  occ_filter.WithResources(images)
  occ_filter.WithCustomFilter(custom_filter)
  return occ_filter.GetChunkifiedFilters()
