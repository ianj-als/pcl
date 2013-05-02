class ResolverVisitor(object):
    def __init__(self):
        self._errors = list()
        self._warnings = list()

    @staticmethod
    def __add_messages(msg_fmt, collection, unpack_fn, msg_collection):
        for entity in collection:
            info = unpack_fn(entity)
            msg_collection.append(msg_fmt % info)

    def _add_errors(self, msg_fmt, collection, unpack_fn):
        ResolverVisitor.__add_messages(msg_fmt,
                                       collection,
                                       unpack_fn,
                                       self._errors)

    def _add_warnings(self, msg_fmt, collection, unpack_fn):
        ResolverVisitor.__add_messages(msg_fmt,
                                       collection,
                                       unpack_fn,
                                       self._warnings)

    def has_errors(self):
        return len(self._errors) > 0

    def get_errors(self):
        return tuple(self._errors)

    def has_warnings(self):
        return len(self._warnings) > 0

    def get_warnings(self):
        return tuple(self._warnings)
