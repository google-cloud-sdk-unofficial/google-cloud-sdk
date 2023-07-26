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
"""Implements the command to upload Generic artifacts to a repository."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts.vex_util import ParseVexFile
from googlecloudsdk.core import properties


@base.ReleaseTracks(
    base.ReleaseTrack.GA
)
@base.Hidden
class LoadVex(base.Command):
  """Load VEX data from a file."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
       To load a CSAF security advisory file given an artifact in Artifact Registry and the file on disk, run:

        $ {command} --uri=us-east1-docker.pkg.dev/project123/repository123/someimage@sha256:49765698074d6d7baa82f --source=/path/to/vex/file --location=us-east1

To load a CSAF security advisory file given an artifact with a tag and a file on disk, run:

        $ {command} --uri=us-east1-docker.pkg.dev/project123/repository123/someimage:latest --source=/path/to/vex/file --location=us-east1
    """,
  }
  ca_client = None
  ca_messages = None

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--uri',
        required=True,
        help='The path of the artifact in Artifact Registry.',
    )
    parser.add_argument(
        '--source',
        required=True,
        help='The path of the VEX file.',
    )
    parser.add_argument(
        '--project',
        required=False,
        help='The parent project to load security advisory into.',
    )
    return

  def Run(self, args):
    """Run the generic artifact upload command."""
    self.ca_client = apis.GetClientInstance('containeranalysis', 'v1')
    self.ca_messages = self.ca_client.MESSAGES_MODULE
    project = args.project
    if project is None:
      project = properties.VALUES.core.project.Get(required=True)
    uri = args.uri
    filename = args.source
    notes, uri_with_digest = ParseVexFile(filename, uri)
    self.writeNotes(notes, project, uri_with_digest)
    return

  def writeNotes(self, notes, project, uri):
    notes_to_create = []
    notes_to_update = []
    notes_to_retain = notes
    for note in notes:
      note_exists = False
      get_request = self.ca_messages.ContaineranalysisProjectsNotesGetRequest(
          name='projects/{}/notes/{}'.format(project, note.key)
      )
      try:
        self.ca_client.projects_notes.Get(get_request)
        note_exists = True
      except apitools_exceptions.HttpNotFoundError:
        note_exists = False
      if note_exists:
        notes_to_update.append(note)
      else:
        notes_to_create.append(note)
    self.batchWriteNotes(notes_to_create, project)
    self.updateNotes(notes_to_update, project)
    self.deleteNotes(notes_to_retain, project, uri)

  def batchWriteNotes(self, notes, project):
    if not notes:
      return
    note_value = self.ca_messages.BatchCreateNotesRequest.NotesValue()
    note_value.additionalProperties = notes
    batch_request = self.ca_messages.BatchCreateNotesRequest(
        notes=note_value,
    )
    request = self.ca_messages.ContaineranalysisProjectsNotesBatchCreateRequest(
        parent='projects/{}'.format(project),
        batchCreateNotesRequest=batch_request,
    )
    self.ca_client.projects_notes.BatchCreate(request)

  def updateNotes(self, notes, project):
    if not notes:
      return
    for note in notes:
      patch_request = (
          self.ca_messages.ContaineranalysisProjectsNotesPatchRequest(
              name='projects/{}/notes/{}'.format(project, note.key),
              note=note.value,
          )
      )
      self.ca_client.projects_notes.Patch(patch_request)

  def deleteNotes(self, file_notes, project, uri):
    list_request = self.ca_messages.ContaineranalysisProjectsNotesListRequest(
        filter='vulnerability_assessment.product.generic_uri="{}"'.format(uri),
        parent='projects/{}'.format(project),
    )
    db_notes = list_pager.YieldFromList(
        service=self.ca_client.projects_notes,
        request=list_request,
        field='notes',
        batch_size_attribute='pageSize'
    )

    cves_in_file = set()
    for file_note in file_notes:
      file_uri = file_note.value.vulnerabilityAssessment.product.genericUri
      file_cve = file_note.value.vulnerabilityAssessment.assessment.cve
      if file_uri == uri:
        cves_in_file.add(file_cve)

    for db_note in db_notes:
      db_cve = db_note.vulnerabilityAssessment.assessment.cve
      if db_cve not in cves_in_file:
        delete_request = (
            self.ca_messages.ContaineranalysisProjectsNotesDeleteRequest(
                name=db_note.name
            )
        )
        self.ca_client.projects_notes.Delete(delete_request)
