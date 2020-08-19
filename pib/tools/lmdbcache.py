import lmdb
import pickle
import pdb

class LMDBCacheAPI:
    def __init__(self, path):
        map_size = 1 << 32
        self.env = lmdb.open(path, map_size=map_size)

    def serialize(self, obj):
        BEST_COMPRESS = 4
        return pickle.dumps(obj, protocol=BEST_COMPRESS)

    def __setitem__(self, key, val):
        with self.env.begin(write=True) as txn:
            key = key.encode("ascii")
            try:
                txn.put(key, val)
            except Exception as e:
                pass

    def __getitem__(self, key):
        key = key.encode("ascii")
        with self.env.begin() as txn:
            record = txn.get(key)
        if record is None:
            return None
        return pickle.loads(record)

    def findkey(self, key):
        key = key.encode("ascii")
        with self.env.begin() as txn:
            record = txn.get(key)
        if record is None:
            return False
        else:
            return True

    def write(self, idx, value):
        sample = self.serialize(value)
        self.__setitem__(idx, sample)

