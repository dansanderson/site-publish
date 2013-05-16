import os
import pprint
from apiclient import discovery
import httplib2
from oauth2client import file, client, tools

CLIENT_ID = '145889693104-t0nm6og9vt8qmrdkus1aecm7d45stcgr.apps.googleusercontent.com'
CLIENT_SECRET = 'FrnHaW-_GEuKGFiF0eSVkEuA'

discovery_doc_fname = os.path.join(
    os.path.dirname(__file__),
    'SitePublishApi.discovery')
discovery_doc = open(discovery_doc_fname).read()
site_publish_service = discovery.build_from_document(discovery_doc)


class Demostart(object):
    @classmethod
    def get_short_desc(cls):
        return 'Demo of the start request. Not for actual use.'

    @classmethod
    def get_long_desc(cls):
        return ''

    def do_cmd(self, args):
        storage = file.Storage('a_credentials_file')
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            flow = client.OAuth2WebServerFlow(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                scope='https://www.googleapis.com/auth/userinfo.email')

            credentials = tools.run(flow, storage)

        http = credentials.authorize(httplib2.Http())

        request = site_publish_service.start(
            body={
                'project_prefixes': ['/foo/'],
                'upload_paths': ['/foo/bar.html', '/foo/baz.png']})
        response = request.execute(http=http)
        pprint.pprint(response)
        return 0
