from .lazy_load import get_tokenizer

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