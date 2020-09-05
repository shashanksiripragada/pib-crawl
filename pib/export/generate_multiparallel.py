from collections import defaultdict
from itertools import combinations, permutations
import os
import pandas as pd
import langid
from argparse import ArgumentParser
from ..cli.utils import ParallelWriter, file_line_count, canonical_lang_pair_dirname

def collect(xx, yy, input_dir, pwriter):
    common = defaultdict(list)
    def dirname(xx):
        fst, snd = sorted([xx, 'en'])
        return '{}-{}'.format(fst, snd)

    dxx = dirname(xx)
    dyy = dirname(yy)
    fname = 'train'
    with open('./{}/{}/{}.{}'.format(input_dir, dxx, fname, xx)) as src1,\
         open('./{}/{}/{}.en'.format(input_dir, dxx, fname)) as tgt1,\
         open('./{}/{}/{}.{}'.format(input_dir, dyy, fname, yy)) as src2,\
         open('./{}/{}/{}.en'.format(input_dir, dyy, fname)) as tgt2:
        
        for s1, t1 in zip(src1, tgt1):
            s1 = s1.strip()
            t1 = t1.strip()
            common[t1].append(s1)

        for s2, t2 in zip(src2, tgt2):
            s2 = s2.strip()
            t2 = t2.strip()
            common[t2].append(s2)


        for l in common:
            if len(common[l]) == 2:
                srcline, tgtline = common[l]
                src_pred , _ = langid.classify(srcline)
                tgt_pred , _ = langid.classify(tgtline)
                if (src_pred, tgt_pred) == (xx, yy):
                    pwriter.write(xx, yy, srcline, tgtline)

def get_stats(langs, input_dir, fpath, fname, stats_output):
    data = defaultdict(int)
    for lang in langs:
        data[lang] = 0

    df = pd.DataFrame(data, index = langs)
    perm = permutations(langs, 2)
    for direction in list(perm):
        direction = sorted(direction)
        xx, yy = direction

        active_dir = fpath 
        if 'en' in direction:
            active_dir = input_dir

        train_file_name = '{}.{}'.format(fname, yy)
        train_file_path = os.path.join(active_dir, canonical_lang_pair_dirname(xx, yy), train_file_name)
        count = file_line_count(train_file_path)
        src, tgt = direction
        a, b = langs.index(src), langs.index(tgt)

        if a > b:
            src, tgt = tgt, src

        df.at[src, tgt] = count

    print("Total samples:", df.values[1:,:].sum())
    df.to_csv(stats_output)

if __name__ == '__main__':
    parser=ArgumentParser()
    parser.add_argument('--input-dir', help='input directory containing xx-en, xx-yy also gets written to this directory',  required=True)
    parser.add_argument('--fpath', help='path to write multilingual data',  required=True)
    parser.add_argument('--fname', help='name to be written',  required=True)
    parser.add_argument('--stats-output', help='Outputs stats file as a CSV',  required=True)

    args = parser.parse_args()
    pwriter = ParallelWriter(args.fpath, args.fname)
    langs = ['en','hi','ta','te','ml','ur','bn','gu','mr','or','pa']

    perm = combinations(langs, 2)
    for xx, yy in list(perm):
        if  'en' not in [xx, yy]:
            print(xx, yy)
            # collect(xx, yy, args.input_dir, pwriter)

    get_stats(langs, args.input_dir, args.fpath, args.fname, args.stats_output)


