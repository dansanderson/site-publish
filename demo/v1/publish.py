#!/usr/bin/env python

"""A simple version of the publishing client tool.

Usage: publish.py <file-or-dir> [<file-or-dir> ...]

Files must be in a directory structure that represents the desired URL paths
of the content on the site.  The directory representing the URL root must
contain a file named _site.yaml.  For example:

    .../mysite/_site.yaml
    .../mysite/index.html
    .../mysite/faq.html
    .../mysite/guide/index.html
    .../mysite/guide/getstarted.html

_site.yaml is a YAML file with the following parameters describing the site to
which the content is published:

    host: "domain.name"
    port: 80
    publishing_path: "/_/content/"
    use_ssl: false

Only site_domain is required.  The other options have default values.

You can override any of these settings for all files being published using
similarly-named command-line options:

    publish.py --host=localhost --port=8080 content/*
"""

import email.mime.base
import email.mime.multipart
import mimetypes
import os
import sys
import urllib2
import yaml


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
      fname: The filename of the file to publish.

    Returns:
       A tuple: (root_dir, site_config)  root_dir is the directory path
       containing the site configuration file (corresponding to the URL root
       of the site). site_config is the parsed config object.  Returns (None,
       None) if a site config file could not be located.
    """
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


def make_upload_url(site_config):
    """Calculates the upload URL for a site based on config.

    Args:
      site_config: The site config object.

    Returns:
      The upload URL.
    """
    return ''.join([
        'https' if site_config.get('use_ssl', False) else 'http',
        '://',
        site_config['host'],
        ':' if 'port' in site_config else '',
        str(site_config.get('port', '')),
        site_config.get('publishing_path', '/_/content/'),
        'upload'])


def make_mime_multipart_string(fname, url_path):
    """Builds a MIME multipart message containing a file to publish.

    Args:
      fname: The filename of the file to publish.
      url_path: The intended site URL path.

    Returns:
      The MIME multipart message, as a string.
    """
    mime_type, encoding = mimetypes.guess_type(fname)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    msg = email.mime.base.MIMEBase(*(mime_type.split('/', 1)))
    with open(fname) as fp:
        msg.set_payload(fp.read())
    msg.add_header('Content-Disposition', 'attachment', filename=url_path)
    multipart = email.mime.multipart.MIMEMultipart()
    multipart.attach(msg)
    return multipart.as_string()


def publish_file(fname):
    """Publishes a file.

    Args:
      fname: The filename of the file to publish.
    """
    if os.path.split(fname)[1].startswith('_'):
        return

    site_root, site_config = get_site_config_for_file(fname)
    url_path = fname[len(site_root):]
    upload_url = make_upload_url(site_config)
    multipart_string = make_mime_multipart_string(fname, url_path)

    sys.stdout.write('%s:%s\n' % (site_config['site_domain'], url_path))
    response = urllib2.urlopen(upload_url, multipart_string)
    if response.getcode() != 200:
        raise Exception('Failed to upload %s' % fname)


def main(args):
    """The main routine."""
    for arg in args:
        if not os.path.exists(arg):
            sys.stderr.write(
                'File or directory %s does not exist, skipping', arg)
        elif os.path.isdir(arg):
            for dirname, dnames, fnames in os.walk(arg):
                for fname in fnames:
                    publish_file(os.path.join(dirname, fname))
        else:
            publish_file(arg)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
