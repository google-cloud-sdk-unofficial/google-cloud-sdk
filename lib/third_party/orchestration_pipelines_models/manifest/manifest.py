# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Module for a Manifest wrapper that provides helper methods."""
from typing import Optional
from orchestration_pipelines_models.manifest.manifest_pb2 import (
    Manifest as ManifestModel,
    VersionHistory,
    VersionMetadata,
)
from cloudsdk.google.protobuf import json_format


class VersionDeploymentInfo:
    """A stable data class for deployment details of a version."""

    def __init__(self,
                 origination: Optional[str] = None,
                 git_repo: Optional[str] = None,
                 git_branch: Optional[str] = None,
                 commit_sha: Optional[str] = None):
        self.origination = origination
        self.git_repo = git_repo
        self.git_branch = git_branch
        self.commit_sha = commit_sha


class Manifest:
    """A wrapper class for the Manifest model to provide helper methods."""

    def __init__(self, manifest: ManifestModel):
        if not isinstance(manifest, ManifestModel):
            raise TypeError("manifest must be a ManifestModel object")
        self._manifest = manifest

    @property
    def manifest(self) -> ManifestModel:
        """Returns the underlying Manifest object."""
        return self._manifest

    @classmethod
    def from_dict(cls, manifest_def: dict) -> Optional["Manifest"]:
        """Creates a Manifest from a dictionary."""
        if manifest_def is None:
            return None
        manifest = ManifestModel()
        json_format.ParseDict(js_dict=manifest_def,
                              message=manifest,
                              ignore_unknown_fields=False)
        return cls(manifest)

    def get_bundle_id(self) -> str:
        """Returns the bundle ID from the manifest."""
        return self._manifest.bundle

    def get_default_version(self) -> str:
        """Returns the default version from the manifest."""
        return self._manifest.default_version

    def is_current(self, version_id: str) -> bool:
        """Checks if a given version is the default version."""
        if not version_id:
            return False
        return self._manifest.default_version == version_id

    def is_paused(self, pipeline_id: str) -> bool:
        """Checks if a pipeline is marked as paused in the manifest."""
        return pipeline_id in self._manifest.paused_pipelines

    def is_pipeline_in_bundle(self, version_id: str, pipeline_id: str) -> bool:
        """Checks if a pipeline is listed in the specified version's history."""
        latest_version_info = self._get_latest_version_history_entry(
            version_id)
        if latest_version_info and latest_version_info.pipelines:
            return pipeline_id in latest_version_info.pipelines
        return False

    def get_deployment_details(
            self, version_id: str) -> Optional[VersionDeploymentInfo]:
        """
        Returns the deployment details for a specific version, taking the most
        recent entry if multiple exist for the same version.
        """

        latest_version_info = self._get_latest_version_history_entry(
            version_id)

        if not latest_version_info or latest_version_info.metadata == VersionMetadata(
        ):
            return None

        pb_deployment_details = latest_version_info.metadata.deployment_details
        origination = latest_version_info.metadata.origination

        return VersionDeploymentInfo(
            origination=origination,
            git_repo=pb_deployment_details.git_repo or None,
            git_branch=pb_deployment_details.git_branch or None,
            commit_sha=pb_deployment_details.commit_sha or None,
        )

    def _get_latest_version_history_entry(
            self, version_id: str) -> Optional[VersionHistory]:
        """Finds the most recent VersionHistory entry for a given version_id."""
        if not self._manifest.versions_history:
            return None
        matching_versions = [
            vh for vh in self._manifest.versions_history
            if vh and vh.version_id == version_id
        ]
        if not matching_versions:
            return None
        matching_versions.sort(key=lambda vh: vh.timestamp, reverse=True)
        return matching_versions[0]
