

def detok(tokenizer, src_out):
    src = []
    for line in src_out:
        src_detok = tokenizer.detokenize(line)
        src.append(src_detok)
    return src

def split_and_wrap_in_p(text):
    lines = text.splitlines()
    wrap = lambda l: '<p>{}</p>'.format(l)
    lines = list(map(wrap, lines))
    return '\n'.join(lines)

def clean_translation(tokenizer, translation):
    lines = translation.translated.splitlines()
    detokenized = detok(tokenizer, lines)
    translated_text = '\n'.join(detokenized)
    return translated_text


LAZY_LOADS = {}
def lazy_load(key):

    def op_model():
        from ilmulti.translator import from_pretrained
        return from_pretrained(tag='mm-to-en-iter3', use_cuda=True)

    def aligner():
        from ilmulti.align import BLEUAligner
        op_model = lazy_load('op_model')
        return BLEUAligner(
                    op_model.translator, op_model.tokenizer,
                    op_model.segmenter
        )


    lambda_wrapped = {
        'op_model' : op_model,
        'aligner': aligner    
    }

    if not key in LAZY_LOADS:
        assert(key in lambda_wrapped)
        LAZY_LOADS[key] = lambda_wrapped[key]()

    return LAZY_LOADS[key]

