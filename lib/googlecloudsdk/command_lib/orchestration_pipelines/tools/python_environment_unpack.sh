#!/bin/bash

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

set -e

# --- Configuration ---
# The GCS path to the archive you want to download and unpack
GCS_ARCHIVE_PATH="@@GCS_ARCHIVE_PATH@@"

# The base local directory on each node
LOCAL_INSTALL_DIR="@@LOCAL_INSTALL_DIR@@"
# The subdirectory where the archive contents will be placed
LIBS_DIR="@@LIBS_DIR@@"

# --- Script Logic ---
ARCHIVE_NAME=$(basename "${GCS_ARCHIVE_PATH}")
LOCAL_TMP_DIR="/tmp/init_action_archive"

ROLE=$(/usr/share/google/get_metadata_value attributes/dataproc-role)
if [[ "${ROLE}" == "Master" ]]; then
  echo "Starting initialization action: Download and Unpack Archive"

  # Create necessary directories
  # mkdir -p will create the parent directories as needed
  mkdir -p "${LIBS_DIR}"
  mkdir -p "${LOCAL_TMP_DIR}"
  mkdir -p "${LOCAL_INSTALL_DIR}"
  rm -rf "${LOCAL_TMP_DIR}"/*
  rm -rf "${LOCAL_INSTALL_DIR}"/*

  # Download the archive from GCS
  echo "Downloading ${GCS_ARCHIVE_PATH} to ${LOCAL_TMP_DIR}"
  if ! gsutil cp "${GCS_ARCHIVE_PATH}" "${LOCAL_TMP_DIR}"; then
    echo "ERROR: Failed to download ${GCS_ARCHIVE_PATH}"
    exit 1
  fi
  echo "Download complete."

  # Unpack the archive into the LIBS_DIR
  echo "Unpacking ${LOCAL_TMP_DIR}/${ARCHIVE_NAME} to ${LIBS_DIR}"
  if ! tar -xzf "${LOCAL_TMP_DIR}/${ARCHIVE_NAME}" -C "${LIBS_DIR}"; then
    echo "ERROR: Failed to unpack ${ARCHIVE_NAME}"
    exit 1
  fi
  echo "Unpacking complete."

  # Unpack the archive into the LOCAL_INSTALL_DIR
  echo "Unpacking ${LOCAL_TMP_DIR}/${ARCHIVE_NAME} to ${LOCAL_INSTALL_DIR}"
  if ! tar -xzf "${LOCAL_TMP_DIR}/${ARCHIVE_NAME}" -C "${LOCAL_INSTALL_DIR}"; then
    echo "ERROR: Failed to unpack ${ARCHIVE_NAME}"
    exit 1
  fi
  echo "Unpacking complete."

  # Make the environment files readable by all users.
  find "${LOCAL_INSTALL_DIR}"  -type f -exec chmod a+r {} \;

  # Clean up the downloaded archive
  rm -f "${LOCAL_TMP_DIR}/${ARCHIVE_NAME}"
  rmdir "${LOCAL_TMP_DIR}"

  echo "Initialization action finished successfully."
  echo "Environment from ${GCS_ARCHIVE_PATH} is now available at ${LIBS_DIR}"
  echo "Environment from ${GCS_ARCHIVE_PATH} is now available at ${LOCAL_INSTALL_DIR}"
fi

