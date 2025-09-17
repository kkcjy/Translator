import argparse
import json
import math
import numpy as np
import mindspore as ms
import mindspore.nn as nn
import mindspore.ops as ops
from mindspore import Tensor
from fastapi import FastAPI
from pydantic import BaseModel

# ==== 特殊 token ====
PAD_TOKEN = "<pad>"
BOS_TOKEN = "<s>"
EOS_TOKEN = "</s>"
UNK_TOKEN = "<unk>"
SPECIAL_TOKENS = [BOS_TOKEN, EOS_TOKEN, PAD_TOKEN, UNK_TOKEN]

app = FastAPI()

# ==== 位置编码 ====
class PositionalEncoding(nn.Cell):
    def __init__(self, d_model, dropout=0.1, max_len=500):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = np.zeros((max_len, d_model))
        position = np.arange(0, max_len).reshape(-1, 1)
        div_term = np.exp(np.arange(0, d_model, 2) * -(math.log(10000.0) / d_model))

        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)
        self.pe = Tensor(pe.astype(np.float32)).unsqueeze(0)

    def construct(self, x):
        x = x + self.pe[:, :x.shape[1]]
        return self.dropout(x)


# ==== 翻译模型 ====
class TranslationModel(nn.Cell):
    def __init__(self, zh_vocab, en_vocab, d_model, max_len, dropout=0.1):
        super(TranslationModel, self).__init__()  # 🔑 必须写在第一行

        self.d_model = d_model
        self.max_len = max_len
        self.zh_vocab = zh_vocab
        self.en_vocab = en_vocab
        self.zh_token_to_id = {tok: idx for idx, tok in enumerate(zh_vocab)}
        self.en_token_to_id = {tok: idx for idx, tok in enumerate(en_vocab)}

        # Embedding
        self.src_embedding = nn.Embedding(len(zh_vocab), d_model,
                                          padding_idx=zh_vocab.index(PAD_TOKEN))
        self.tgt_embedding = nn.Embedding(len(en_vocab), d_model,
                                          padding_idx=en_vocab.index(PAD_TOKEN))

        # Positional Encoding
        self.positional_encoding = PositionalEncoding(d_model, dropout, max_len)

        # Transformer
        self.transformer = nn.Transformer(
            d_model=d_model,
            nhead=8,
            num_encoder_layers=6,
            num_decoder_layers=6,
            dim_feedforward=1024,
            dropout=dropout,
            batch_first=True
        )

        # 输出层
        self.predictor = nn.Dense(d_model, len(en_vocab))

        # 提前生成mask
        self.tgt_mask_full = self.generate_square_subsequent_mask(max_len)

    def generate_square_subsequent_mask(self, size):
        mask = np.triu(np.ones((size, size)), k=1).astype(np.bool_)
        return Tensor(mask, dtype=ms.bool_)

    def construct(self, src, tgt):
        src_emb = self.src_embedding(src) * math.sqrt(self.d_model)
        tgt_emb = self.tgt_embedding(tgt) * math.sqrt(self.d_model)
        src_emb = self.positional_encoding(src_emb)
        tgt_emb = self.positional_encoding(tgt_emb)

        tgt_len = tgt.shape[1]
        tgt_mask = self.tgt_mask_full[:tgt_len, :tgt_len]

        out = self.transformer(
            src=src_emb,
            tgt=tgt_emb,
            tgt_mask=tgt_mask
        )
        logits = self.predictor(out)
        return logits

    def infer(self, src_sentence, max_length=64, beam_width=5):
        """中文 → 英文翻译 (beam search)"""
        zh_tokens = [BOS_TOKEN] + list(src_sentence) + [EOS_TOKEN]
        zh_ids = [self.zh_token_to_id.get(t, self.zh_token_to_id[UNK_TOKEN]) for t in zh_tokens]

        if len(zh_ids) > max_length:
            zh_ids = zh_ids[:max_length]
        else:
            zh_ids += [self.zh_token_to_id[PAD_TOKEN]] * (max_length - len(zh_ids))

        src = Tensor([zh_ids], dtype=ms.int32)

        pad_id_en = self.en_token_to_id[PAD_TOKEN]
        eos_id = self.en_token_to_id[EOS_TOKEN]
        bos_id = self.en_token_to_id[BOS_TOKEN]

        hypotheses = [([bos_id], 0.0)]

        for i in range(max_length - 1):
            new_hypotheses = []
            for hyp, score in hypotheses:
                tgt_seq = hyp + [pad_id_en] * (max_length - len(hyp))
                tgt = Tensor([tgt_seq], dtype=ms.int32)

                output = ops.stop_gradient(self(src, tgt))
                logits = output[0, i, :]
                probs = ops.softmax(logits, axis=-1)

                top_k_probs, top_k_tokens = ops.top_k(probs, k=beam_width)
                top_k_tokens = top_k_tokens.asnumpy().astype(np.int32)
                top_k_probs = top_k_probs.asnumpy()

                for j in range(beam_width):
                    token_id = top_k_tokens[j]
                    prob = top_k_probs[j]
                    new_score = score - np.log(prob + 1e-9)
                    new_hypotheses.append((hyp + [token_id], new_score))

            hypotheses = sorted(new_hypotheses, key=lambda x: x[1])[:beam_width]

            if all(hyp[-1] == eos_id for hyp, _ in hypotheses):
                break

        best_hyp = hypotheses[0][0]

        translated_tokens = []
        for _id in best_hyp[1:]:
            if _id == eos_id:
                break
            translated_tokens.append(self.en_vocab[_id])

        translated_sentence = ' '.join([t for t in translated_tokens if t not in SPECIAL_TOKENS])
        return translated_sentence


# ==== 工具函数 ====
def load_vocab(vocab_path):
    with open(vocab_path, 'r', encoding='utf-8') as f:
        vocab_data = json.load(f)
    if isinstance(vocab_data, dict) and 'vocab' in vocab_data:
        return vocab_data['vocab']
    elif isinstance(vocab_data, list):
        return vocab_data
    else:
        raise ValueError(f"Unsupported vocab format in {vocab_path}")

def model_translate():
    return 1

class TranslationRequest(BaseModel):
    text: str
    direction: str
    model: str

@app.post("/")
def translate(req: TranslationRequest):
    if req.direction == "zh-en":
        result = model_translate(req.model, req.text, req.direction)
        return {req.model: result}
    else:
        assert("only the translation direction from Chinese to English is allowed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chinese → English Translation (Single Sentence)")
    parser.add_argument('--model_path', type=str,default=r"TRS/zh_en/TRS_zh_en.ckpt")
    parser.add_argument('--zh_vocab_path', type=str, default=r"TRS/zh_en/zh_vocab.json")
    parser.add_argument('--en_vocab_path', type=str, default=r"TRS/zh_en/en_vocab.json")
    parser.add_argument('--d_model', type=int, default=256)
    parser.add_argument('--max_length', type=int, default=64)
    parser.add_argument('--sentence', type=str, default="今天天气真好", help="中文输入句子")
    args = parser.parse_args()

    # 加载词表
    zh_vocab = load_vocab(args.zh_vocab_path)
    en_vocab = load_vocab(args.en_vocab_path)

    # 初始化模型
    model = TranslationModel(zh_vocab, en_vocab, args.d_model, args.max_length)
    param_dict = ms.load_checkpoint(args.model_path)
    ms.load_param_into_net(model, param_dict)
    model.set_train(False)

    # 翻译
    translated = model.infer(args.sentence, max_length=args.max_length)
    print(f"输入: {args.sentence}")
    print(f"翻译: {translated}")