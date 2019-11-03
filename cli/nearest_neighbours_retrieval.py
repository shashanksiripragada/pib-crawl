
from webapp.retrieval import get_candidates,reorder, preprocess, tfidf,retrieve_neighbours_en

def store_retrieved():
    queries = db.session.query(Translation)\
                        .all()
    for q in tqdm(queries):
        if q.translated:
            exists = Retrieval.query.filter(Retrieval.query_id==q.parent_id).first()
            if not exists:
                try:
                    retrieved = retrieve_neighbours_en(q.parent_id)
                except:
                    print(q.parent_id,file=error)
                    continue
                else:
                    retrieved_id = retrieved[0][0]
                    score = retrieved[0][1]   
                    entry = Retrieval(query_id=q.parent_id, retrieved_id=retrieved_id, score=score)
                    try:
                        db.session.add(entry)
                        db.session.commit()
                    except:
                        print(q.parent_id,file=error)
#store_retrieved()

if __name__ == '__main__':
    pass
