from cli import ILMULTI_DIR

def get_translator():
    from ilmulti.translator.pretrained import mm_all
    root = os.path.join(ILMULTI_DIR, 'mm-all')
    translator = mm_all(root=root, use_cuda=True).get_translator()
    return translator

def get_aligner():
    aligner = BLEUAligner(translator, tokenizer, segmenter)
    return aligner
