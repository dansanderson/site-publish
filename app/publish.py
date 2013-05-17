import logging

from google.appengine.api import taskqueue
from google.appengine.ext import ndb

import models


@ndb.transactional
def start_change(project_prefixes, upload_paths, current_user):
    """Starts a change.

    This function uses a datastore transaction to create a Change entity with
    a monotonically increasing ID.  It gets this ID from the ChangeGroup
    singleton entity, which stores the last-used ID and also serves as the
    entity group root for all Change entities.

    Args:
      project_prefixes: A list of URL prefixes to use to calculate which paths
        should be deleted.
      upload_paths: A list of URL paths that exist and may be uploaded.
      current_user: The users.User starting the change.

    Returns:
      The Change model, saved to the datastore.
    """
    change_group_key = ndb.Key('ChangeGroup', '1')
    change_group = change_group_key.get()
    if not change_group:
        change_group = models.ChangeGroup(
            key=change_group_key,
            next_id=1)

    next_id = change_group.next_id
    change_group.next_id += 1
    change_group.put()

    change_key = models.Change.get_key(next_id)
    change = models.Change(
        key=change_key,
        upload_paths=upload_paths,
        project_prefixes=project_prefixes,
        created_by=current_user)
    change.put()
    return change


def create_content(change_id, url_path, content_type, data):
    """Store uploaded content.

    This function uses a datastore transaction to create a Content entity for
    uploaded content.

    Args:
      change_id: The ID of the change, as an int.
      url_path: The URL path of the content being uploaded.
      content_type: The MIME content type for the data.
      data: The data of the content.
    """
    content_key = models.Content.get_key(url_path, change_id)
    content = models.Content(
        key=content_key,
        content_type=content_type,
        data=data)
    content.put()


@ndb.transactional
def commit_change(change_id):
    # TODO: Better error handling.

    change_key = models.Change.get_key(change_id)
    change = change_key.get()
    if change is None:
        raise Exception('Invalid change ID')
    if change.is_committed or change.is_aborted:
        raise Exception('Cannot commit a finished change.')

    change.is_committed = True
    change.put()
    taskqueue.add(url='/_sitepublish/apply', params={'change_id': change_id})
