from io import StringIO
from ilmulti.utils.language_utils import inject_token
from ilmulti.segment import SimpleSegmenter, Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from collections import defaultdict
from copy import deepcopy
from urduhack.tokenization import sentence_tokenizer
f=open('translate_error.txt','a')
class Batch:
    def __init__(self, uids, lines, state):
        #self.uids = uids
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
        return self

    def __next__(self):
        # Return a single batch
        batch = self.next_batch()
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
        update_flag = True
        while(update_flag):
            entry = self.entries[self.index]
            flag = self.filter_f(entry)

            if not entry.content:
                print('{} {} has no content, skipping entry'.format(entry.lang, entry.id))
                self.index = self.index+1
            
            if flag:
                print('{} {} has translation for specified model, skipping entry'.format(entry.lang, entry.id))
                self.index = self.index+1

            if entry.content and not flag:             
                _uids, _lines, max_len, token_count = self.get_entry(entry)
                current_ptpb = len(_lines) * max_len
                if current_ptpb > self.max_tokens:
                    # skip very large entries
                    self.index = self.index + 1

                future_state = deepcopy(state)
                def update_state_dict(state):
                    #look ahead for update
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
                    state.update(future_state)
            state['epb'] += 1    

            if self.index > len(self.entries):
                break
        return Batch(uids, lines, state)


'''
def collect(batches):
    list of entries, ready to be written
'''      
class Preproc:
    def __init__(self, segmenter, tokenizer):
        self.segmenter = segmenter
        self.tokenizer = tokenizer

    def create_stringio(self, lines, lang):
        tokenized = [ ' '.join(self.tokenizer(line, lang=lang)[1]) \
                for line in lines ]
        lstring = '\n'.join(tokenized)
        return tokenized, StringIO(lstring)

    def process(self, content, lang):
        if lang == 'ur':
            lang, segments = sentence_tokenizer(entry.content)
            tokenized, _io = self.create_stringio(segments, lang)
            return tokenized, _io
        lang, segments = self.segmenter(content, lang=lang)
        tokenized, _io = self.create_stringio(segments, lang)
        return tokenized, _io

    def detok(self, src_out):
        src = []
        for line in src_out:
            src_detok = self.tokenizer.detokenize(line)
            src.append(src_detok)
        return src   
