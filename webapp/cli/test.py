import sys
sys.path.insert(1, '../')
from io import StringIO
from argparse import ArgumentParser
from collections import defaultdict
from tqdm import tqdm
from utils import Preproc
from ilmulti.segment import Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from ilmulti.translator.pretrained import mm_all
from ilmulti.align import BLEUAligner
from ilmulti.utils.language_utils import inject_token
from webapp import db
from webapp.models import Entry, Link, Translation, Retrieval
from webapp.retrieval import retrieve_neighbours_en
from urduhack.tokenization import sentence_tokenizer

segmenter = Segmenter()
tokenizer = SentencePieceTokenizer()
root = '/home/darth.vader/.ilmulti/mm-all'
translator = mm_all(root=root).get_translator()
aligner = BLEUAligner(translator, tokenizer, segmenter)
preproc = Preproc(segmenter, tokenizer)
lang = 'ur'
#model = ['mm_all', 'mm_all_iter0']
def get_sents(lang):
    entries = db.session.query(Entry).filter(Entry.lang==lang).all()
    for entry in entries:
        print(entry.id, entry.content, '\n\n\n')
        lang, segments = segmenter(entry.content, lang=lang)
        segments = '\n'.join(segments)
        #segments = [s[::-1] for s in segments]
        ur_tok = sentence_tokenizer(entry.content)
        ur_tok = '\n'.join(ur_tok)
        print(segments, '\n\n\n')
        print(ur_tok)
        break

get_sents(lang)


#langs = ['en', 'ml', 'ur', 'te', 'hi', 'pa', 'kn', 'or', 'as', 'gu', 'mr', 'ta', 'bn']
'''


langs = ['ml', 'ur', 'te', 'hi', 'ta', 'bn']


def paralle_write(src_entry, src_lang, tgt_entry, tgt_lang, q_id, r_id):
    print('##########Article {} #########'.format(q_id),file=src_file)
    print(src_entry,file=src_file)
    print('##########Article {} #########'.format(r_id),file=tgt_file)
    print(tgt_entry,file=tgt_file)


from sqlalchemy import or_, and_
import itertools
from ilmulti.segment import SimpleSegmenter, Segmenter
segmenter = Segmenter()

def get_lines_words(content, lang):
    #lines = content.splitlines()
    _, lines = segmenter(content, lang=lang)
    lines = [l for l in lines if l]
    words = [line.split() for line in lines]
    words = list(itertools.chain.from_iterable(words))
    return len(lines), len(words)


def get_lines_words_en(content, lang):
    from nltk.tokenize import sent_tokenize
    lines = content.splitlines()
    lines = [sent_tokenize(l) for l in lines]
    lines = list(itertools.chain.from_iterable(lines))
    words = [line.split() for line in lines]
    words = list(itertools.chain.from_iterable(words))
    return len(lines), len(words)

def evaluate_retrieval(qcontent, qlang, rcontent, rlang):
    qlines, qwords = get_lines_words(qcontent, qlang)
    rlines, rwords = get_lines_words_en(rcontent, rlang)   
    ldiff = abs(qlines-rlines)
    wdiff = abs(qwords-rwords)
    if ldiff<=5 and wdiff<=50:
        return True


def retrieve_bn():
    count = 0
    queries = db.session.query(Entry.id,Entry.content,Translation.translated,Translation.parent_id)\
                        .filter(and_(Entry.lang=='bn', Translation.parent_id==Entry.id))\
                        .all()
    for q in queries:
        if q.translated:
            r_id = db.session.query(Retrieval.retrieved_id)\
                    .filter(Retrieval.query_id==q.parent_id)\
                    .first().retrieved_id
            r = db.session.query(Entry.content).filter(Entry.id==r_id)\
                          .first()
            hyp = q.translated
            isalign = evaluate_retrieval(q.content,'bn', r.content,'en')
            if isalign:
                _ , src_io = process(q.content, 'bn')
                _ , tgt_io = process(r.content, 'en')
                hyp_io = StringIO(hyp)
                src_aligned , tgt_aligned = aligner.bleu_align(src_io, tgt_io, hyp_io)
                src_aligned = detok(src_aligned)
                tgt_aligned = detok(tgt_aligned)               
                src_entry = '\n'.join(src_aligned)
                tgt_entry = '\n'.join(tgt_aligned)
                paralle_write(src_entry, 'bn', tgt_entry, 'en', q.id, r_id)
            #margins = [scores[0]-scores[i] for i in range(1,len(scores))]

if __name__ == '__main__':
    parser=ArgumentParser()
    parser.add_argument('src_lang', help='non-english language')
    parser.add_argument('tgt_lang', help='english is the target language')
    args = parser.parse_args()
    src_lang, tgt_lang = args.src_lang, args.tgt_lang
    src_file = open('pib_en-{}.{}.txt'.format(src_lang, src_lang),'a')
    tgt_file = open('pib_en-{}.{}.txt'.format(src_lang, tgt_lang),'a')
    retrieve_bn()
#retrieve('hi')


langs = ['en', 'ml', 'ur', 'te', 'hi', 'pa', 'or', 'gu', 'mr', 'ta', 'bn']


def count_len(segments):
    segs = []
    for segment in segments:
        if segment!='' and "*" not in segment:
            segs.append(segment)
    return len(segs)


'''
