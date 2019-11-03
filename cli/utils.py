from io import StringIO
from ilmulti.utils.language_utils import inject_token
from ilmulti.segment import SimpleSegmenter, Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer

segmenter = Segmenter()
tokenizer = SentencePieceTokenizer()

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
