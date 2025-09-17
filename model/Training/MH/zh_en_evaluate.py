import argparse
import os
import math
import itertools
import json
import logging
import numpy as np
import mindspore as ms
import mindspore.nn as nn
import mindspore.ops as ops
from mindspore import Tensor
from tqdm import tqdm
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

PAD_TOKEN = "<pad>"
BOS_TOKEN = "<s>"
EOS_TOKEN = "</s>"
UNK_TOKEN = "<unk>"
SPECIAL_TOKENS = [BOS_TOKEN, EOS_TOKEN, PAD_TOKEN, UNK_TOKEN]

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TranslationModel(nn.Cell):
    def __init__(self, zh_vocab, en_vocab, d_model, max_len, dropout=0.1):
        super(TranslationModel, self).__init__()
        self.d_model = d_model
        self.max_len = max_len

        self.zh_vocab = zh_vocab
        self.en_vocab = en_vocab
        self.zh_token_to_id = {tok: idx for idx, tok in enumerate(zh_vocab)}
        self.en_token_to_id = {tok: idx for idx, tok in enumerate(en_vocab)}

        pad_idx = zh_vocab.index(PAD_TOKEN)
        self.src_embedding = nn.Embedding(len(zh_vocab), d_model, padding_idx=pad_idx)
        pad_idx_tgt = en_vocab.index(PAD_TOKEN)
        self.tgt_embedding = nn.Embedding(len(en_vocab), d_model, padding_idx=pad_idx_tgt)
        self.positional_encoding = PositionalEncoding(d_model, dropout, max_len)

        self.transformer = nn.Transformer(
            d_model=d_model,
            nhead=8,
            num_encoder_layers=6,
            num_decoder_layers=6,
            dim_feedforward=1024,
            dropout=dropout,
            batch_first=True
        )

        self.predictor = nn.Dense(d_model, len(en_vocab))

        self.tgt_mask_full = self.generate_square_subsequent_mask(max_len)

    def generate_square_subsequent_mask(self, size):
        mask = np.triu(np.ones((size, size)), k=1).astype(np.bool_)
        return Tensor(mask, dtype=ms.bool_)

    def construct(self, src, tgt):
        pad_id_src = self.zh_token_to_id[PAD_TOKEN]
        pad_id_tgt = self.en_token_to_id[PAD_TOKEN]

        src_key_padding_mask = (src == pad_id_src)
        tgt_key_padding_mask = (tgt == pad_id_tgt)

        src_emb = self.src_embedding(src) * math.sqrt(self.d_model)
        tgt_emb = self.tgt_embedding(tgt) * math.sqrt(self.d_model)

        src_emb = self.positional_encoding(src_emb)
        tgt_emb = self.positional_encoding(tgt_emb)

        tgt_len = tgt.shape[1]
        tgt_mask = self.tgt_mask_full[:tgt_len, :tgt_len]

        out = self.transformer(
            src=src_emb,
            tgt=tgt_emb,
            src_key_padding_mask=src_key_padding_mask,
            tgt_key_padding_mask=tgt_key_padding_mask,
            tgt_mask=tgt_mask
        )

        pred = self.predictor(out)
        return pred

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

            all_eos = True
            for hyp, _ in hypotheses:
                if hyp[-1] != eos_id:
                    all_eos = False
                    break
            if all_eos:
                break

        best_hyp = hypotheses[0][0]

        translated_tokens = []
        for _id in best_hyp[1:]:
            if _id == eos_id:
                break
            translated_tokens.append(self.en_vocab[_id])

        translated_sentence = ' '.join([t for t in translated_tokens if t not in SPECIAL_TOKENS])

        return translated_sentence


class PositionalEncoding(nn.Cell):
    def __init__(self, d_model, dropout, max_len=500):
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


def load_vocab(vocab_path):
    """加载JSON格式的词汇表"""
    with open(vocab_path, 'r', encoding='utf-8') as f:
        vocab_data = json.load(f)
    if isinstance(vocab_data, dict) and 'vocab' in vocab_data:
        return vocab_data['vocab']
    elif isinstance(vocab_data, list):
        return vocab_data
    else:
        raise ValueError(f"Unsupported vocab format in {vocab_path}")


def load_test_data(test_data_path, start_line=500001, max_samples=500):
    test_data = []
    with open(test_data_path, 'r', encoding='utf-8') as f:
        for line in itertools.islice(f, start_line, None):
            parts = line.strip().split(',', 1)
            if len(parts) == 2:
                chinese, english = parts
                test_data.append((chinese.strip(), english.strip()))
            if len(test_data) >= max_samples:
                break
    return test_data


def evaluate_model(model, test_data, max_length=64):
    smooth = SmoothingFunction().method4
    total_bleu, count = 0.0, 0
    results = []

    for zh_text, en_text in tqdm(test_data, desc="Evaluating"):
        translated = model.infer(zh_text, max_length)
        reference = en_text.lower().split()
        candidate = translated.split()
        bleu = sentence_bleu([reference], candidate, smoothing_function=smooth)
        total_bleu += bleu
        count += 1

        results.append({
            "source": zh_text,
            "reference": en_text,
            "translation": translated,
            "bleu": bleu
        })

    avg_bleu = total_bleu / count if count > 0 else 0.0
    return avg_bleu, results


def main():
    parser = argparse.ArgumentParser(description='Evaluate Zh→En Translation Model')
    parser.add_argument('--model_path', type=str, required=True)
    parser.add_argument('--zh_vocab_path', type=str, required=True)
    parser.add_argument('--en_vocab_path', type=str, required=True)
    parser.add_argument('--test_data_path', type=str, required=True)
    parser.add_argument('--d_model', type=int, default=256)
    parser.add_argument('--max_length', type=int, default=64)
    parser.add_argument('--output_dir', type=str, default='./evaluation_results')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # 加载词汇表
    zh_vocab = load_vocab(args.zh_vocab_path)
    en_vocab = load_vocab(args.en_vocab_path)

    test_data = load_test_data(args.test_data_path)

    model = TranslationModel(zh_vocab, en_vocab, args.d_model, args.max_length)
    param_dict = ms.load_checkpoint(args.model_path)
    ms.load_param_into_net(model, param_dict)
    model.set_train(False)

    avg_bleu, results = evaluate_model(model, test_data, args.max_length)
    results_path = os.path.join(args.output_dir, 'zh2en_results.json')
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump({'average_bleu': avg_bleu, 'samples': results}, f, ensure_ascii=False, indent=2)

    print(f"Average BLEU score: {avg_bleu:.4f}")
    for i, r in enumerate(results[:5]):
        print(f"{i + 1}. Source: {r['source']}")
        print(f"   Reference: {r['reference']}")
        print(f"   Translation: {r['translation']}")
        print(f"   BLEU: {r['bleu']:.4f}")


if __name__ == "__main__":
    main()