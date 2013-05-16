import webapp2

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


class ApplyTask(webapp2.RequestHandler):
    def post(self):
        change_id = self.request.params['change_id']

        # TODO:
        # 1) For each project_root, query Path for subpaths.
        # 2) Compare existing subpaths with upload_paths.  The difference is
        #     the list of paths to delete.
        # 3) Update Paths and delete old Content objects, as
        #     appropriate.  It's probably best to trigger new tasks to
        #     handle these.


app = webapp2.WSGIApplication(
    [('/_sitepublish/apply', ApplyTask),
     ('/.*', View)],
    debug=True)
