import os
import sys
from tqdm import tqdm
from .. import db
from ..models import Entry, Link, Translation, Retrieval
from ..retrieval import retrieve_neighbours_en
from sqlalchemy import func, and_
from argparse import ArgumentParser
from ilmulti.translator import from_pretrained

def store_retrieved(model, langs, force_redo=False, resume_from=0):    
    op_model = from_pretrained(tag=model, use_cuda=True)
    queries = (
        Translation.query.filter(
            and_(
                Translation.model==model, 
            )
        ).all()
    )

    counter = 0
    for query in tqdm(queries):
        if counter < resume_from:
            counter += 1
            continue;

        counter += 1
        if query.translated:
            retrieval_entry = (
                Retrieval.query.filter(
                    and_(
                        Retrieval.query_id==query.parent_id,
                        Retrieval.model==model
                    )
                ).first()
            )
            if not retrieval_entry or force_redo:
                retrieved = retrieve_neighbours_en(query.parent_id, op_model.tokenizer, model=model)
                first = retrieved[0]
                retrieved_id, score = first
                if retrieval_entry:
                    retrieval_entry.retrieved_id = retrieved_id
                    retrieval_entry.score = score

                else:
                    retrieval_entry = Retrieval(
                            query_id=query.parent_id, retrieved_id=retrieved_id,
                            score=score, model=model)

                db.session.add(retrieval_entry)
                db.session.commit()

if __name__ == '__main__':
    langs = ['hi', 'ta', 'te', 'ml', 'bn', 'gu', 'mr', 'pa', 'or']#, 'ur']
    # langs = ['ml']
    parser=ArgumentParser()
    parser.add_argument('--model', help='retrieval based on model used for tanslation', required=True)
    parser.add_argument('--resume-from', help='', default=0, type=int)
    parser.add_argument('--force-redo', help='', action='store_true')
    args = parser.parse_args()
    store_retrieved(args.model, langs, args.force_redo, args.resume_from)

