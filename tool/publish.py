import os
from apiclient import discovery
import httplib2
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client.tools import run

CLIENT_ID = '145889693104-t0nm6og9vt8qmrdkus1aecm7d45stcgr.apps.googleusercontent.com'
CLIENT_SECRET = 'FrnHaW-_GEuKGFiF0eSVkEuA'

discovery_doc_fname = os.path.join(
    os.path.dirname(__file__),
    'SitePublishApi.discovery')
discovery_doc = open(discovery_doc_fname).read()
site_publish_service = discovery.build_from_document(discovery_doc)


class Publish(object):
    @classmethod
    def get_short_desc(cls):
        return 'PUBLISH SHORT DESC'

    @classmethod
    def get_long_desc(cls):
        return 'PUBLISH LONG DESC'

    def do_cmd(self, args):
        print 'I DID THE COMMAND: %r' % args

        storage = Storage('a_credentials_file')
        credentials = storage.get()

        if credentials is None or credentials.invalid == True:
          flow = OAuth2WebServerFlow(
              client_id=CLIENT_ID,
              client_secret=CLIENT_SECRET,
              scope='https://www.googleapis.com/auth/userinfo.email')

          credentials = run(flow, storage)

        http = credentials.authorize(httplib2.Http())

        request = site_publish_service.start(
            body={
                'project_prefixes': ['/foo/'],
                'upload_paths': ['/foo/bar.html', '/foo/baz.png']})
        response = request.execute(http=http)
        import pprint; pprint.pprint(response)
        return 0
