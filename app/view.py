import logging
import webapp2
from google.appengine.ext import ndb

import models


class View(webapp2.RequestHandler):
    def get(self):
        url_path = self.request.path
        if url_path.endswith('/'):
            url_path += 'index.html'

        path_key = models.Path.get_key(url_path)
        path = path_key.get()
        if path and not path.is_deleted:
            content = path.content_key.get()
            assert content is not None

            self.response.headers['Content-Type'] = \
                content.content_type.encode('utf-8')
            self.response.out.write(content.data)
            self.response.md5_etag()
        else:
            self.response.status = 404


@ndb.transactional
def apply_delete_path(path, change_id):
    path_obj = models.Path.get_key(path).get()
    path_obj.content_key.delete()
    path_obj.is_deleted = True
    path_obj.last_applied_change_id = change_id
    path_obj.put()


@ndb.transactional
def apply_update_path(path, change_id):
    path_obj = models.Path.get_key(path).get()

    if path_obj is not None and not path_obj.is_deleted:
        path_obj.content_key.delete()

    if path_obj is None:
        path_obj = models.Path(key=models.Path.get_key(path))

    path_obj.content_key = models.Content.get_key(path, change_id)
    path_obj.is_deleted = False
    path_obj.last_applied_change_id = change_id
    path_obj.put()


class ApplyTask(webapp2.RequestHandler):
    def post(self):
        change_id = int(self.request.params['change_id'])
        change = models.Change.get_key(change_id).get()

        existing_paths = set()
        for project_root in change.project_prefixes:
            query = models.Path.query()
            existing_paths.add(list(query.iter(keys_only=True)))
        paths_to_delete = existing_paths - set(change.upload_paths)

        # To improve the maximum change size, defer these steps to
        # multiple sub-tasks.  As written, this is limited by the 10
        # minute task size.

        for path_to_delete in paths_to_delete:
            apply_delete_path(path_to_delete, change_id)

        for path_to_update in change.upload_paths:
            apply_update_path(path_to_update, change_id)


app = webapp2.WSGIApplication(
    [('/_sitepublish/apply', ApplyTask),
     ('/.*', View)],
    debug=True)
