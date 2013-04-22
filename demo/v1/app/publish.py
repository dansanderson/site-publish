import email.parser
import logging
import webapp2

import models


class UploadContent(webapp2.RequestHandler):
    def post(self):
        mime_parser = email.parser.Parser()
        msg_root = mime_parser.parse(self.request.body_file)
        rpcs = []

        for part in msg_root.get_payload():
            content = models.Content(
                key=models.Content.get_key(part.get_filename()),
                content_type=part.get_content_type(),
                data=part.get_payload())
            rpcs.append(content.put_async())
            logging.info('Received upload for path %s', part.get_filename())

        for rpc in rpcs:
            rpc.check_success()


app = webapp2.WSGIApplication(
    [('/_/content/upload', UploadContent)],
    debug=True)
