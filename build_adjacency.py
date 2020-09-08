from collections import defaultdict, Counter
from pib import db
from pib.models import FrozenLink

class AdjacencyBuilder:
    def __init__(self):
        self.adj = defaultdict(list)

    def add_edges(self, edges):
        for u, v in edges:
            self.adj[v].append(u)
            # self.adj[u].append(v)

    def _stats(self):
        ls = [len(self.adj[v]) for v in self.adj]
        return Counter(ls)


    def __str__(self):
        # return self._stats().__str__()
        from pprint import pprint, pformat
        return pformat(self.adj, indent=4)

    def populate(self, db):
        for u in self.adj:
            vs = self.adj[u]
            for v in vs:
                link = FrozenLink(anchor_id=u, other_id=v)
                db.session.add(link)

        db.session.commit()
    

if __name__ == '__main__':
    files = [
        "mm-to-en-iter3-aligned-bn-en.txt",
        "mm-to-en-iter3-aligned-gu-en.txt",
        "mm-to-en-iter3-aligned-hi-en.txt",
        "mm-to-en-iter3-aligned-ml-en.txt",
        "mm-to-en-iter3-aligned-mr-en.txt",
        "mm-to-en-iter3-aligned-or-en.txt",
        "mm-to-en-iter3-aligned-pa-en.txt",
        "mm-to-en-iter3-aligned-ta-en.txt",
        "mm-to-en-iter3-aligned-te-en.txt",
        "mm-to-en-iter3-aligned-ur-en.txt",
    ]

    def process_line(line):
        u, v = list(map(int, line.split()))
        return u, v
    
    builder = AdjacencyBuilder()

    for _file in files:
        with open(_file) as fp:
            lines = fp.read().splitlines()
            pairs = list(map(process_line, lines))
            builder.add_edges(pairs)


    print(builder)
    # builder.populate(db)

