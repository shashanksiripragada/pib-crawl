from io import StringIO
from ilmulti.utils.language_utils import inject_token
from ilmulti.segment import SimpleSegmenter, Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer

segmenter = Segmenter()
tokenizer = SentencePieceTokenizer()


class Batch:
    def __init__(self, uids, lines):
        #self.uids = uids
        self.uids = uids
        self.lines = lines
        self.target = None

    def set_target(self, target):
        self.target = target   

class BatchBuilder:
    def __init__(self, entries, max_tokens, tgt_lang, max_lines=None, filter_f=lambda x: True):
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

    def create_stringio(self, lines, lang):
        tokenized = [ ' '.join(tokenizer(line, lang=lang)[1]) \
                for line in lines ]
        lstring = '\n'.join(tokenized)
        return tokenized, StringIO(lstring)

    def process(self, content, lang):
        lang, segments = segmenter(content, lang=lang)
        tokenized, _io = self.create_stringio(segments, lang)
        return tokenized, _io


    def get_entry(self, entry):
        #print('{} doesnot have translation'.format(entry.id))
        uids, lines = [], []
        tokenized_lines ,_ = self.process(entry.content, entry.lang)
        injected_lines = inject_token(tokenized_lines, self.tgt_lang)
        uid_list = ['{} {}'.format(entry.id, count) for count, line in enumerate(injected_lines) ]
        max_len = max([ len(line.split()) for line in injected_lines ])
        token_count = self.count_tokens(injected_lines)
        return uid_list, injected_lines, max_len, token_count


    def next_batch(self):
        uids, lines = [], []
        current_tokens = 0
        max_length = 0
        tokens = 0
        sizes = []
        while(current_tokens < self.max_tokens):
            entry = self.entries[self.index]
            flag = self.filter_f(entry)
            if flag:
                print('{} has translation for specified model, skipping entry'.format(entry.id))
            if entry.content and not flag:
                _uids, _lines, max_len, token_count = self.get_entry(entry)
                uids.extend(_uids)
                lines.extend(_lines)
                max_length = max(max_length, max_len)
                #tokens += token_count
                current_tokens += max_length * len(lines)
            self.index = self.index + 1
            if self.index > len(self.entries):
                break
        return Batch(uids, lines)


'''
def collect(batches):
    list of entries, ready to be written
'''      

def inject_lang_token(content, tgt_lang):
    lang, content = segmenter(content)
    output = []
    for line in content:
        if line:
            lang, _tokens = tokenizer(line)
            _out = ' '.join(_tokens)
            output.append(_out)        
    injected_toks = inject_token(output,tgt_lang) 
    return injected_toks 

def detok(src_out):
    src = []
    for line in src_out:
        src_detok = tokenizer.detokenize(line)
        src.append(src_detok)
    return src   

def create_stringio(lines, lang):
    tokenized = [ ' '.join(tokenizer(line, lang=lang)[1]) \
            for line in lines ]
    lstring = '\n'.join(tokenized)
    return tokenized, StringIO(lstring)

def process(content, lang):
    lang, segments = segmenter(content, lang=lang)
    tokenized, _io = create_stringio(segments, lang)
    return tokenized, _io