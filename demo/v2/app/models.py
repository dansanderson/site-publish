from google.appengine.ext import ndb


class Content(ndb.Model):
    # Key = URL path for the file
    data = ndb.BlobProperty()
    content_type = ndb.StringProperty()
    last_updated_time = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def get_key(cls, path):
        return ndb.Key(cls, path)
