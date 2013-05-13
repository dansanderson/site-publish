from google.appengine.ext import ndb


class ChangeGroup(ndb.Model):
    next_id = ndb.IntegerProperty(required=True)


class Change(ndb.Model):
    upload_paths = ndb.StringProperty(repeated=True)
    project_prefixes = ndb.StringProperty(repeated=True)
    created_by = ndb.UserProperty()
    is_committed = ndb.BooleanProperty(default=False)
    is_aborted = ndb.BooleanProperty(default=False)

    def get_change_id(self):
        return int(self.key.string_id())

    @classmethod
    def get_key(cls, change_id):
        return ndb.Key(ChangeGroup, '1', cls, '%012d' % change_id)


class Path(ndb.Model):
    content_key = ndb.KeyProperty()
    is_deleted = ndb.BooleanProperty(default=False)
    last_applied_change_id = ndb.IntegerProperty()

    @classmethod
    def get_key(cls, path):
        return ndb.Key(cls, path)


class Content(ndb.Model):
    data = ndb.BlobProperty()
    content_type = ndb.StringProperty()

    @classmethod
    def get_key(cls, path, change_id):
        return ndb.Key(Path, path, cls, str(change_id))
