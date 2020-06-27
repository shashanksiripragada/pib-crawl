import os
import sys
from tqdm import tqdm
from webapp import db
from webapp.models import Entry, Link, Translation, Retrieval
from webapp.retrieval import retrieve_neighbours_en
from sqlalchemy import func, and_
from argparse import ArgumentParser


def store_retrieved(model, langs):    
    
    entries = Entry.query.filter(
                    Entry.lang.in_(langs)
                ).all()

    entry_ids = [entry.id for entry in entries]
    
    queries =   Translation.query.filter(
                    and_(
                        Translation.model==model, 
                        Translation.parent_id.in_(entry_ids)
                    )
                ).all()

    for query in tqdm(queries):
        if query.translated:
            exists = Retrieval.query.filter(
                        and_(
                            Retrieval.query_id==query.parent_id,
                            Retrieval.model==model
                        )
                    ).first()

            if not exists:
                try:
                    retrieved = retrieve_neighbours_en(query.parent_id, model)
                except:
                    print(query.parent_id,file=error)
                    continue
                else:
                    retrieved_id = retrieved[0][0]
                    score = retrieved[0][1]   
                    entry = Retrieval(
                                query_id=query.parent_id, 
                                retrieved_id=retrieved_id,
                                score=score, 
                                model=model
                            )
                    try:
                        db.session.add(entry)
                        db.session.commit()
                    except:
                        print(query.parent_id,file=error)

if __name__ == '__main__':
    langs = ['hi', 'ta', 'te', 'ml', 'bn', 'gu', 'mr', 'pa', 'or', 'ur']
    parser=ArgumentParser()
    parser.add_argument('--model', help='retrieval based on model used for tanslation', required=True)
    args = parser.parse_args()
    model = args.model
    error = open('retrieval_error.txt', 'a')
    store_retrieved(model, langs)