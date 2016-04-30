import string
import json


ALLOWED = frozenset(string.ascii_letters + string.digits + '_-')

class InvalidNameException(Exception):
    pass

class DataStore:
    _store = {}
    _file = ""
    _encoder = None
    _decoder = None

    def __init__(self, name, encoder=None, decoder=None, sanitize=False):
        self._encoder = encoder
        self._decoder = decoder
        self._load(name, sanitize)

    def __iter__(self):
        return self._store.__iter__()
    
    def items(self):
        return self._store.items()

    def _load(self, name, sanitize=False):
        if frozenset(name) <= ALLOWED:
            self._file = name + ".json"
        elif sanitize == True:
            self._file = ''.join([c for c in name if c in ALLOWED]) + ".json"
        else:
            raise InvalidNameException
        try:
            with open(self._file, "r") as db:
                self._store = json.load(db, object_hook=self._decoder)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            self._store = {}

    def _save(self):
        with open(self._file, "w") as db:
            json.dump(self._store, db, ensure_ascii=True, cls=self._encoder)

    def sync(self):
        self._save()

    def insert(self, name, obj):
        name = name.lower()
        if name not in self._store:
            self._store[name] = obj
            self._save()
        else:
            raise KeyError

    def update(self, name, obj):
        name = name.lower()
        if name in self._store:
            self._store[name] = obj
            self._save()
        else:
            raise KeyError

    def delete(self, name):
        name = name.lower()
        if name in self._store:
            del self._store[name]
            self._save()
        else:
            raise KeyError

    def select(self, name):
        name = name.lower()
        return self._store[name]
        


if __name__ == '__main__':
    # db = TagDB()
    
    # print(db.deletemass(None, None, True))
    
    # print(db.inserttag("channel", "ownerid", "Title", "content"))
    # print(db.inserttag("channel", "ownerid2", "Title2", "content"))
    # print(db.inserttag("channel2", "ownerid", "2Title", "content"))
    
    # print(dict(db.selecttag("channel", "title")))
    # print([dict(tag) for tag in db.searchtag("channel", "e")])
    # print([dict(tag) for tag in db.searchtag("channel2", "e")])
    # print(db.deletemass("channel", "ownerid"))
    # print("---")
    # print([dict(tag) for tag in db.searchtag("channel", "e")])
    # print([dict(tag) for tag in db.searchtag("channel2", "e")])

    print("Done")
