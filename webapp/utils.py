from .lazy_load import get_tokenizer

def detok(src_out):
    src = []
    tokenizer = get_tokenizer()
    for line in src_out:
        src_detok = tokenizer.detokenize(line)
        src.append(src_detok)
    return src

def split_and_wrap_in_p(text):
    lines = text.splitlines()
    wrap = lambda l: '<p>{}</p>'.format(l)
    lines = list(map(wrap, lines))
    return '\n'.join(lines)
