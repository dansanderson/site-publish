"""Routines and command-line driver for publishing content."""

# TODO: better service error reporting
# TODO: catch ctrl-C and issue abort request if necessary
# TODO: multithreaded uploads
# TODO: not-modified check
# TODO: large upload support

import httplib2
import mimetypes
import os
import yaml
from apiclient import discovery
from oauth2client import file, client, tools

USER_CONFIG_DIR = '~/.site-publish'
CREDENTIALS_FILENAME = 'credentials'
CLIENT_ID = ('145889693104-t0nm6og9vt8qmrdkus1aecm7d45stcgr'
             '.apps.googleusercontent.com')
CLIENT_SECRET = 'FrnHaW-_GEuKGFiF0eSVkEuA'


def get_service():
    """Generates the service object from the discovery document.

    The discovery document is expected to be in the tool's source
    location, named SitePublishApi.discovery.

    Returns:
      The service instance.
    """
    # TODO: make discovery doc path overrideable at the command line

    discovery_doc_fname = os.path.join(
        os.path.dirname(__file__),
        'SitePublishApi.discovery')
    discovery_doc = open(discovery_doc_fname).read()
    site_publish_service = discovery.build_from_document(discovery_doc)
    return site_publish_service


def get_authorized_http():
    """Create an httplib2.Http wrapped with OAuth credentials.

    This checks the user's configuration directory for stored
    credentials.  If found, it uses them.  If not found, this opens a
    browser window to prompt the user to sign in and authorize access
    to the user's email address, then stores the credentials.

    Returns:
      The wrapped Http instance.
    """
    # TODO: make config dir path overrideable at the command line
    # TODO: command line option to disable browser prompt (and just fail)

    user_config_path = os.path.expanduser(USER_CONFIG_DIR)
    if not os.path.exists(user_config_path):
        os.makedirs(user_config_path)
    credentials_path = os.path.join(user_config_path, CREDENTIALS_FILENAME)

    storage = file.Storage(credentials_path)
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        flow = client.OAuth2WebServerFlow(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            scope='https://www.googleapis.com/auth/userinfo.email')

        credentials = tools.run(flow, storage)

    http = credentials.authorize(httplib2.Http())
    return http


def load_config(config_fname):
    """Loads a YAML configuration file.

    Args:
      config_fname: The filename of the config file.

    Returns:
      The parsed Python object for the YAML file's contents.
    """
    with open(config_fname) as fh:
        return (os.path.dirname(config_fname), yaml.load(fh))


# A cache of directory paths mapped to site configuration, to reduce the
# number of stat calls in get_site_config_for_file().
_site_config_cache = {}


def get_site_config_for_file(fname):
    """Gets the site configuration for a file to be published.

    A content file resides in a directory structure that contains a _site.yaml
    configuration file in the directory representing the site's URL path root.
    This function locates the file, loads it if necessary, then returns the
    directory path for the configuration file and the parsed configuration
    object.  Already-parsed site configuration is cached to avoid excessive
    work.

    In a typical case, all requested files use the same site config, but this
    supports publishing to multiple sites with one run of the command.

    Args:
      fname: The path of the directory or file to publish.

    Returns:
       A tuple: (root_dir, site_config)  root_dir is the directory path
       containing the site configuration file (corresponding to the URL root
       of the site). site_config is the parsed config object.  Returns (None,
       None) if a site config file could not be located.
    """
    if os.path.isdir(fname):
        dname = fname
    else:
        dname = os.path.dirname(fname)

    dnames_tested = []
    while dname != '/':
        if dname in _site_config_cache:
            return _site_config_cache[dname]

        dnames_tested.append(dname)
        config_fname = os.path.join(dname, '_site.yaml')
        if os.path.exists(config_fname):
            config = load_config(config_fname)
            for tested in dnames_tested:
                _site_config_cache[tested] = config
            return config

        dname = os.path.dirname(dname)
    return (None, None)


def is_hidden(file_path):
    """Returns true if the file should not be uploaded to the site.

    A file is hidden if its name or the name of any parent directory
    begins with an underscore.  For example, these files are not
    published to the site, even if they appear in a content source
    directory:
      /foo/bar/_baz.dat
      /foo/_templates/base.html

    Args:
      file_path: The filesystem path for the file.
    """
    hidden_parts = [p for p in file_path.split('/') if p.startswith('_')]
    return len(hidden_parts) > 0


class Publish(object):
    @classmethod
    def get_short_desc(cls):
        return 'Publishes content files to the website.'

    @classmethod
    def get_long_desc(cls):
        return '''
Usage:
  sp publish <dir-or-file> [<dir-or-file>...]
'''

    def do_cmd(self, args):
        project_prefixes = []
        # uploads is a list of (file_path, url_path)
        uploads = []

        for arg in args:
            path = os.path.normpath(os.path.expanduser(arg))

            if is_hidden(path):
                continue

            if os.path.isdir(path):
                # Treat directory as a project path, and add its files.
                (root_dir, site_config) = get_site_config_for_file(path)
                project_path = path[len(root_dir):]
                project_prefixes.append(project_path)
                for dname, _, fnames in os.walk(path):
                    for fname in fnames:
                        file_path = os.path.join(dname, fname)
                        if is_hidden(file_path):
                            continue
                        url_path = file_path[len(root_dir):]
                        uploads.append((file_path, url_path))

            elif os.path.isfile(path):
                (root_dir, site_config) = get_site_config_for_file(path)
                url_path = path[len(root_dir):]
                uploads.append((path, url_path))

            else:
                print 'Path %s is not a file or directory, skipping' % arg

        http = get_authorized_http()
        service = get_service()

        # Start the change.
        request = service.start(
            body={
                'project_prefixes': project_prefixes,
                'upload_paths': [p[1] for p in uploads]})
        response = request.execute(http=http)
        change_id = response['change_id']

        # Upload files.
        for (file_path, url_path) in uploads:
            mime_type, encoding = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            with open(file_path) as fh:
                data = fh.read()
            request = service.upload(
                body={
                    'change_id': change_id,
                    'url_path': url_path,
                    'content_type': mime_type,
                    'data': data})
            response = request.execute(http=http)
            del data

        # Commit change.
        request = service.commit(body={'change_id': change_id})
        response = request.execute(http=http)

        return 0
