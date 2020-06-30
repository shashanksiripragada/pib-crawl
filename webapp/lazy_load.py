
translator = None

def get_translator():
    from ilmulti.translator import from_pretrained
    if translator is None:
        translator = from_pretrained(tag='mm-all-iter0').translator
    return translator

def get_aligner():
    translator = get_translator()
    aligner = BLEUAligner(translator, tokenizer, segmenter)
    return aligner

def get_tokenizer():
    from ilmulti.sentencepiece import build_tokenizer
    tokenizer = build_tokenizer('ilmulti-v1')
    return tokenizer

