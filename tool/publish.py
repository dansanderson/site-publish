class Publish(object):
    @classmethod
    def get_short_desc(cls):
        return 'PUBLISH SHORT DESC'

    @classmethod
    def get_long_desc(cls):
        return 'PUBLISH LONG DESC'

    def do_cmd(self, args):
        print 'I DID THE COMMAND: %r' % args
        return 0
