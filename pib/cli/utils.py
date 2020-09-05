import os
from io import StringIO
from ilmulti.utils.language_utils import inject_token
from collections import defaultdict
from copy import deepcopy

class Batch:
    def __init__(self, uids, lines, state):
        self.uids = uids
        self.lines = lines
        self.target = None
        self.state = state

    def set_target(self, target):
        self.target = target   

class BatchBuilder:
    def __init__(self, segmenter, tokenizer, entries, max_tokens, tgt_lang, max_lines=None, filter_f=lambda x: True):
        self.preproc = Preproc(segmenter, tokenizer)
        self.filter_f = filter_f
        self.entries = entries
        self.max_tokens = max_tokens
        self.tgt_lang = tgt_lang

    def __iter__(self):
        self.index = 0
        self.last_index = -1
        return self

    def __next__(self):
        # Return a single batch
        batch = self.next_batch()
        assert (self.index > self.last_index), "Index isn't incremented"
        self.last_index = self.index
        return batch
    
    def count_tokens(self, lines):
        content_length = 0
        for line in lines:
            line = line.split()
            content_length += len(line)
        return content_length

    def get_entry(self, entry):
        #print('{} doesnot have translation'.format(entry.id))
        uids, lines = [], []
        tokenized_lines ,_ = self.preproc.process(entry.content, entry.lang)
        injected_lines = inject_token(tokenized_lines, self.tgt_lang)
        uid_list = ['{} {}'.format(entry.id, count) for count, line in enumerate(injected_lines) ]
        max_len = max([ len(line.split()) for line in injected_lines ])
        token_count = self.count_tokens(injected_lines)
        return uid_list, injected_lines, max_len, token_count

    def next_batch(self):
        uids, lines = [], []
        state = defaultdict(int)

        # while buffer-has-space =>  pool in entries.
        # once entries are done => construct batch.
        check_next = True

        while(check_next):
            entry = self.entries[self.index]
            flag = self.filter_f(entry)

            if not entry.content:
                print('{} {} has no content, skipping entry'.format(entry.lang, entry.id))
                self.index = self.index+1
                state['epb'] += 1    
            
            elif flag:
                print('{} {} has translation for specified model, skipping entry'.format(entry.lang, entry.id))
                self.index = self.index+1
                state['epb'] += 1    

            else:
                _uids, _lines, max_len, token_count = self.get_entry(entry)
                future_state = deepcopy(state)
                def update_state_dict(state):
                    # look ahead for update
                    state['max_length'] = max(state['max_length'], max_len)
                    state['tpb'] += token_count
                    num_lines = len(lines)+len(_lines)
                    state['ptpb'] = state['max_length'] * num_lines 

                update_state_dict(future_state)
                update_flag = future_state['ptpb'] < self.max_tokens
                if update_flag:
                    uids.extend(_uids)
                    lines.extend(_lines)
                    self.index = self.index + 1
                    state['epb'] += 1    
                    state.update(future_state)

                elif (not update_flag) and (not lines):
                    self.index = self.index + 1
                    state['epb'] += 1    
                    check_next = True
                else:
                    check_next = False

            if self.index > len(self.entries):
                break

        assert (uids and lines), "Batch returned empty uids and lines"
        return Batch(uids, lines, state)


class Preproc:
    def __init__(self, segmenter, tokenizer):
        self.segmenter = segmenter
        self.tokenizer = tokenizer

    def create_stringio(self, lines, lang):
        line_buffer = []
        merged_lines = []
        for line in lines:
            lang, tokens = self.tokenizer(line, lang=lang)
            merged_lines.append(tokens)

        tokenized = [ ' '.join(line) for line in merged_lines]
        lstring = '\n'.join(tokenized)
        return tokenized, StringIO(lstring)

    def process(self, content, lang):
        lang, segments = self.segmenter(content, lang=lang)
        # Clean empty lines.
        non_empty_segments = []
        for segment in segments:
            if segment.strip():
                non_empty_segments.append(segment)

        tokenized, _io = self.create_stringio(segments, lang)
        return tokenized, _io

    def detok(self, src_out):
        src = []
        for line in src_out:
            src_detok = self.tokenizer.detokenize(line)
            src.append(src_detok)
        return src   

class ParallelWriter:
    def __init__(self, fpath, fname, unique = False):
        self.fpath = fpath
        self.fname = fname
        self.files = {}
        self.unique = unique
        if self.unique:
            self._tracking_set = set()
            # TODO(jerin): Write this later.
            self._src_tracking_set = set()
            self._tgt_tracking_set = set()

    def get_fp(self, src, tgt):
        fst, snd = sorted([src, tgt])
        dirname = '{}-{}'.format(fst, snd)
        fpath = os.path.join(self.fpath, dirname)
        
        if not os.path.exists(fpath):
            os.makedirs(fpath)

        if (src, tgt) not in self.files:
            self.files[(src, tgt)] = [
                open(os.path.join(fpath, '{}.{}'.format(self.fname, src)), 'w'),
                open(os.path.join(fpath, '{}.{}'.format(self.fname, tgt)), 'w')
            ]

        return self.files[(src, tgt)]

    def write(self, src, tgt, srcline, tgtline):
        if self.unique:
            tpl = (srcline, tgtline)
            add_flag = tpl not in self._tracking_set
            if add_flag:
                self._tracking_set.add(tpl)
                self._write(src, tgt, srcline, tgtline)
        else:
            self._write(src, tgt, srcline, tgtline)


    def _write(self, src, tgt, srcline, tgtline):
        srcfile, tgtfile = self.get_fp(src, tgt)
        print(srcline, file=srcfile)
        print(tgtline, file=tgtfile)

def file_line_count(fpath):
    count = 0
    with open(fpath) as fp:
        for line in fp:
            count += 1
    return count

def canonical_lang_pair_dirname(xx, yy):
    fst, snd = sorted([xx, yy])
    return '{}-{}'.format(fst, snd)
