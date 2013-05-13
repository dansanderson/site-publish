import webapp2

import models


class View(webapp2.RequestHandler):
    def get(self):
        url_path = self.request.path
        if url_path.endswith('/'):
            url_path += 'index.html'
        content_key = models.Content.get_key(url_path)
        content = content_key.get()

        if content:
            self.response.headers['Content-Type'] = \
                content.content_type.encode('utf-8')
            self.response.out.write(content.data)
            self.response.md5_etag()
        else:
            self.response.status = 404


app = webapp2.WSGIApplication(
    [('/.*', View)],
    debug=True)
