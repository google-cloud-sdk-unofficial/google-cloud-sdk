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
"""Git context management for orchestration pipelines."""

import hashlib
import pathlib

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log

ENV_PACK_FILE = "environment.tar.gz"


class GitError(exceptions.Error):
  """Exception for errors during git operations."""
  pass


class SafeCommitSha:
  """A helper class to represent a commit SHA that might be dirty."""

  def __init__(self, git_context):
    self._git_context = git_context

  def __str__(self):
    """Returns the SHA string, checking for dirty state if necessary."""
    self._git_context.EnforceClean()
    if not self._git_context.commit_sha:
      raise GitError(
          "--local mode generates a version hash that cannot be used "
          "for COMMIT_SHA. Please provide COMMIT_SHA explicitly."
      )
    return self._git_context.commit_sha

  def __repr__(self):
    return self._git_context.commit_sha


class GitContext:
  """Manages git status and commit SHA."""

  def __init__(
      self, subprocess_mod, override_version=None,
      bundle_path=None, is_local=False
  ):
    self._subprocess = subprocess_mod
    self._override_version = override_version
    self.is_explicit_version = bool(override_version)
    self._bundle_path = bundle_path
    self._is_local = is_local
    self._version = None
    self._commit_sha = None
    self._is_dirty = False
    self._changes = []
    self._Load()

  def _Load(self):
    """Loads git status and SHA."""

    if self.is_explicit_version:
      self._version = self._override_version
      self._commit_sha = self._override_version
      self._is_dirty = False
      return

    if self._is_local:
      self._commit_sha = None
      content_hash = self._GetContentHash()
      self._version = "local-{}".format(content_hash)
      self._is_dirty = False
      return

    try:
      self._changes = self._GetUncommittedChanges()
      self._is_dirty = bool(self._changes)
    except (self._subprocess.CalledProcessError, FileNotFoundError):
      # No git repo or command failed -> Ignore
      self._is_dirty = False

    try:
      if self._bundle_path:
        try:
          computed_sha = self._subprocess.check_output(
              ["git", "rev-parse", f"HEAD:{self._bundle_path.name}"],
              text=True,
              stderr=self._subprocess.DEVNULL,
          ).strip()
          self._version = computed_sha
          self._commit_sha = computed_sha
          return
        except self._subprocess.CalledProcessError:
          pass

      computed_sha = (
          self._subprocess.check_output(
              ["git", "rev-parse", "HEAD"],
              text=True,
              stderr=self._subprocess.DEVNULL,
          ).strip()
      )
      self._version = computed_sha
      self._commit_sha = computed_sha
    except (self._subprocess.CalledProcessError, FileNotFoundError):
      self._version = None
      self._commit_sha = None

  def _GetUncommittedChanges(self):
    """Returns a list of uncommitted changes, or empty list if clean."""
    try:
      status_output = self._subprocess.check_output(
          ["git", "status", "--porcelain"], text=True
      ).strip()
      if status_output:
        lines = status_output.splitlines()
        ignored_patterns = [".pyc", "__pycache__", ENV_PACK_FILE]
        real_changes = [
            l for l in lines if not any(p in l for p in ignored_patterns)
        ]
        return real_changes
      return []
    except self._subprocess.CalledProcessError:
      return []

  def GetSafeCommitSha(self):
    return SafeCommitSha(self)

  def EnforceClean(self):
    """Enforces that the working copy is clean."""
    if not self._is_dirty:
      return

    real_changes = self._GetUncommittedChanges()
    if real_changes:
      formatted_changes = "\n".join([f"  - {l}" for l in real_changes])
      msg = "Uncommitted changes detected!\n%s" % formatted_changes
      log.error(msg)
      raise GitError(
          "Please commit or stash changes before deploying."
      )

  @property
  def version(self):
    return self._version

  @property
  def commit_sha(self):
    return self._commit_sha

  def CalculateVersionId(self):
    """Calculates the version ID based on SHA."""
    self.EnforceClean()
    version_str = self._version
    if not version_str:
      raise GitError(
          "Could not determine git version ID. "
          "Git history not found. "
          "Ensure you are inside an initialized repository."
      )

    return version_str

  def _GetContentHash(self):
    """Generates a deterministic hash based strictly on source file contents."""
    bundle_path = self._bundle_path
    if bundle_path is None:
      bundle_path = pathlib.Path.cwd()
    ignored_patterns = {
        "__pycache__",
        ".pyc",
        ".pyo",
        ".git",
        ".DS_Store",
        ENV_PACK_FILE,
    }

    content_hashes = []
    for path in bundle_path.rglob("*"):
      if any(part in ignored_patterns for part in path.parts):
        continue

      if path.is_file():
        if path.name.startswith(".") or path.name.endswith(".log"):
          continue
        try:
          file_content = path.read_bytes()
          file_hash = hashlib.sha256(file_content).hexdigest()
          content_hashes.append(file_hash)
        except (IOError, OSError, PermissionError):
          continue

    content_hashes.sort()

    final_hasher = hashlib.sha256()
    for h in content_hashes:
      final_hasher.update(h.encode())

    return final_hasher.hexdigest()[:12]

  def CheckAncestry(self, remote_sha, env):
    """Verifies that the remote version is an ancestor of the local version.

    Args:
      remote_sha: The git commit hash of the remote version.
      env: The target environment for the deployment.

    Returns:
      True if the remote_sha is an ancestor of local_sha, or if the check is
      skipped (e.g., in 'dev' environment or if remote_sha is not found). False
      otherwise.
    """
    if not remote_sha:
      return True

    if str(remote_sha).startswith("local-"):
      log.status.Print(
          "Initial non-local deployment detected; skipping ancestry check."
      )
      return True

    if self._is_local:
      log.status.Print("Local deployment; skipping ancestry check.")
      return True

    try:
      self._subprocess.check_call(
          ["git", "cat-file", "-t", remote_sha],
      )
    except self._subprocess.CalledProcessError:
      if env == "dev":
        log.warning(
            "Remote version %s unknown locally. Proceeding (DEV mode).",
            remote_sha,
        )
        return True
      log.error("Remote version %s not found in local git history.", remote_sha)
      return False

    try:
      self._subprocess.check_call(
          [
              "git",
              "merge-base",
              "--is-ancestor",
              remote_sha,
              self._version,
          ]
      )
      return True
    except self._subprocess.CalledProcessError:
      if env == "dev":
        log.warning(
            "Regression detected: Remote version %s is ahead of local version"
            " %s. Proceeding (DEV mode).",
            remote_sha,
            self._version,
        )
        return True
      log.error(
          "REGRESSION BLOCKED: The remote version (%s) is ahead of your local"
          " version (%s). Please pull the latest changes before deploying.",
          remote_sha,
          self._version,
      )
      return False

  def ValidateAncestryOrRaise(self, remote_version, env, bypass=False):
    """Validates that the remote version in the manifest is safe to overwrite.

    Args:
      remote_version: The git commit hash of the remote version.
      env: The target environment for the deployment.
      bypass: If True, skips the ancestry check (rollbacks).

    Returns:
        The remote_version string if safe (or None if no manifest exists).

    Raises:
        GitError: If the remote version is ahead of the local version.
    """
    if not remote_version:
      return None

    if bypass:
      log.status.Print(
          f"Bypassing ancestry check for remote version {remote_version}."
      )
      return remote_version

    if not self.CheckAncestry(remote_version, env):
      raise GitError(
          f"REGRESSION BLOCKED: The remote version ({remote_version}) "
          "is ahead of or divergent from your local version.\n"
          "Please 'git pull' the latest changes before deploying."
      )
    return remote_version
