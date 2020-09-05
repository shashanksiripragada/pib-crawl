import os
from io import StringIO
from argparse import ArgumentParser
from langid.langid import LanguageIdentifier
from langid.langid import model as m
from ilmulti.translator import from_pretrained
from ..cli.utils import ParallelWriter

class LengthRatioFilter:
    def __init__(self, tokenizer, src_lang, tgt_lang, min_length, lower_bound,
            upper_bound):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.tokenizer = tokenizer
        self.min_length = min_length
    
    def __call__(self, src_line, tgt_line):
        _, src_tokens = self.tokenizer(src_line, lang=self.src_lang)
        _, tgt_tokens = self.tokenizer(tgt_line, lang=self.tgt_lang)
        src_len, tgt_len = len(src_tokens), len(tgt_tokens)

        # Also handles the zero degeneracy
        src = (src_len >= self.min_length)
        tgt = (tgt_len >= self.min_length)
        if not (src and tgt):
            return False

        ratio = src_len/tgt_len
        return (self.lower_bound <= ratio) and (ratio <= self.upper_bound)


class EvalLang:
    def __init__(self, src_lang, tgt_lang, threshold=0.8):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.identifier = LanguageIdentifier.from_modelstring(m, norm_probs=True)
        self.identifier.set_languages([src_lang, tgt_lang])
        self.threshold = threshold

    def __call__(self, src_line, tgt_line):
        slang, src_prob = self.identifier.classify(src_line)
        tlang, tgt_prob = self.identifier.classify(tgt_line)
        src = (src_prob >= self.threshold)
        tgt = (tgt_prob >= self.threshold)
        if (slang == self.src_lang and tlang==self.tgt_lang and src and tgt):
            return True
        else:
            return False


def filter_lines(args):

    fpath = os.path.join(args.output_dir, args.model)

    accepted = ParallelWriter(fpath, fname='train', unique=True)
    rejected = ParallelWriter(fpath, fname='rejected')

    # Open aligned files with directory assumptions.
    dirname = '{}-{}'.format(*sorted([args.src_lang, args.tgt_lang]))
    src_aligned = open(os.path.join(fpath, dirname, 'aligned.{}'.format(args.src_lang)), 'r')
    tgt_aligned = open(os.path.join(fpath, dirname, 'aligned.{}'.format(args.tgt_lang)), 'r')
    
    # engine loaded for tokenizer. Consistency between export model.
    engine = from_pretrained(tag=args.model, use_cuda=False)
    filters = [
        EvalLang(args.src_lang, args.tgt_lang),
        LengthRatioFilter(engine.tokenizer, args.src_lang, args.tgt_lang,
            min_length=2, lower_bound=0.5, upper_bound=2.0)
    ]

    for src_line, tgt_line in zip(src_aligned, tgt_aligned):
        src_line = src_line.rstrip('\n')
        tgt_line = tgt_line.rstrip('\n')

        # Check if any of the filters fail.
        allowed_in = True
        for _filter in filters:
            if not _filter(src_line, tgt_line):
                allowed_in = False

        # Otherwise.
        if allowed_in:
            accepted.write(args.src_lang, args.tgt_lang, src_line, tgt_line)
        
        else:
            rejected.write(args.src_lang, args.tgt_lang, src_line, tgt_line)                    

if __name__ == '__main__':
    parser=ArgumentParser()
    parser.add_argument('--output-dir', help='Output-directory', type=str, required=True)
    parser.add_argument('--src-lang', help='source language, non-english', required=True)
    parser.add_argument('--tgt-lang', help='target language', default='en')
    parser.add_argument('--model', help='translation model for generating dataset', default='mm-to-en-iter2')
    args = parser.parse_args()
    filter_lines(args)

