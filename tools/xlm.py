import torch
xlmr = torch.hub.load('pytorch/fairseq', 'xlmr.large.v0')
xlmr.eval()


hi_tokens = xlmr.encode('नमस्ते दुनिया','नमस्ते दुनिया')
#assert hi_tokens.tolist() == [0, 68700, 97883, 29405, 2]
#xlmr.decode(hi_tokens) 
print(hi_tokens)