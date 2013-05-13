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


app = webapp2.WSGIApplication(
    [('/.*', View)],
    debug=True)
