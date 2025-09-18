import os
import math
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import torch
import torch.nn as nn
from tokenizers import Tokenizer                            # 分词工具
from torchtext.vocab import build_vocab_from_iterator       # 构建词典
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
from torch.nn.functional import pad, log_softmax            # pad用于文本对齐
from transformers import AutoTokenizer

import matplotlib.pyplot as plt
import numpy as np
infer_model=None
en_vocab=None
zh_vocab=None
class TranslationRequest(BaseModel):
    source_text: str
@asynccontextmanager
async def lifespan(app:FastAPI):
    global infer_model,en_vocab,zh_vocab
    try:
        # 加载英文词典
        en_vocab = torch.load(en_vocab_file)
        print(f"✅ 成功加载英文词典，词典大小：{len(en_vocab)}")

        # 加载中文词典
        zh_vocab = torch.load(zh_vocab_file)
        print(f"✅ 成功加载中文词典，词典大小：{len(zh_vocab)}")
        # ----------------------------------------------------------------------------
        print("中文词典大小:", len(zh_vocab))
        print(dict((i, zh_vocab.lookup_token(i)) for i in range(10)))
        # 重新初始化与训练一致的模型结构
        infer_model = TranslationModel(d_model=200, src_vocab=en_vocab, tgt_vocab=zh_vocab)
        # 加载最优模型参数
        checkpoint = torch.load(best_model_path, map_location=device)
        infer_model.load_state_dict(checkpoint['model_state_dict'])
        # 切换为评估模式
        infer_model = infer_model.eval()
        # 移到指定设备
        infer_model = infer_model.to(device)
        print(f"✅ 最优模型加载完成，当前模式：eval，设备：{device}")
    except Exception as e:
        print(f"模型加载失败: {str(e)}")
        raise  # 模型加载失败时终止服务启动
    yield

app=FastAPI(lifespan=lifespan)

# ========== 选择设备（优先GPU，无则用CPU） ==========
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f"当前使用设备: {device}")  # 输出应显示cuda:0（GPU）或cpu

# 加载基础的分词器模型，使用的是基础的bert模型。`uncased`意思是不区分大小写
tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-uncased")

# 分词封装
def en_tokenizer(line):
    """
    定义英文分词器
    :param line: 一句英文句子，例如"I'm learning Deep learning."
    :return: subword分词后的结果，例如：['i', "'", 'm', 'learning', 'deep', 'learning', '.']
    """
    # 使用bert进行分词，直接获取tokens
    return tokenizer.tokenize(line)

en_filepath = r"D:\homework\homework\Summer\files\train.en"
def yield_en_tokens():
    """
    每次yield一个分词后的英文句子，之所以yield方式是为了节省内存。
    如果先分好词再构造词典，那么将会有大量文本驻留内存，造成内存溢出。
    """
    with open(en_filepath, encoding='utf-8') as fd:
        for line in fd:
            yield en_tokenizer(line)

en_tok = yield_en_tokens()
for t in  en_tok:
    print(t)
    break

en_vocab_file = "D:/homework/homework/Summer/files/vocab_en.pt"


zh_filepath = r"D:\homework\homework\Summer\files\train.zh"
def zh_tokenizer(line):
    """
    定义中文分词器
    :param line: 中文句子，例如：机器学习
    :return: 分词结果，例如['机','器','学','习']
    """
    return list(line.strip().replace(" ", ""))


def yield_zh_tokens():
    with open(zh_filepath, encoding='utf-8') as fd:
        for line in fd:
            yield zh_tokenizer(line)

zh_tok = yield_zh_tokens()
for t in  zh_tok:
    print(t)
    break

zh_vocab_file = "D:/homework/homework/Summer/files/vocab_zh.pt"


max_length = 72


def collate_fn(batch):
    """
    将dataset的数据进一步处理，并组成一个batch。
    :param batch: 一个batch的数据，例如：
                  [([6, 8, 93, 12, ..], [62, 891, ...]),
                  ....
                  ...]
    :return: 填充后的且等长的数据，包括src, tgt, tgt_y, n_tokens
             其中src为原句子，即要被翻译的句子
             tgt为目标句子：翻译后的句子，但不包含最后一个token
             tgt_y为label：翻译后的句子，但不包含第一个token，即<bos>
             n_tokens：tgt_y中的token数，<pad>不计算在内。
    """
    # 定义'<bos>'的index，在词典中为0，所以这里也是0
    bs_id = torch.tensor([0])
    # 定义'<eos>'的index
    eos_id = torch.tensor([1])
    # 定义<pad>的index
    pad_id = 2
    # 用于存储处理后的src=en和tgt=zh
    src_list, tgt_list = [], []

    # 循环遍历句子对儿
    for (_src, _tgt) in batch:
        """
        _src: 英语句子，例如：`I love you`对应的index
        _tgt: 中文句子，例如：`我 爱 你`对应的index
        """
        # 将<bos>，句子index和<eos>拼到一块
        processed_src = torch.cat([bs_id, torch.tensor(_src, dtype=torch.int64), eos_id], dim=0)  # 按照行链接
        processed_tgt = torch.cat([bs_id, torch.tensor(_tgt, dtype=torch.int64), eos_id], dim=0)

        """
        将长度不足的句子进行填充到max_padding的长度的，然后增添到list中

        pad：假设processed_src为[0, 1136, 2468, 1349, 1]
             第二个参数为: (0, 72-5)
             第三个参数为：2
        则pad的意思表示，给processed_src左边填充0个2，右边填充67个2。
        最终结果为：[0, 1136, 2468, 1349, 1, 2, 2, 2, ..., 2]
        """
        processed_src = pad(processed_src, (0, max_length - len(processed_src)), value=pad_id)
        src_list.append(processed_src)
        processed_tgt = pad(processed_tgt, (0, max_length - len(processed_tgt)), value=pad_id)
        tgt_list.append(processed_tgt)

    # 将多个src句子堆叠到一起
    src = torch.stack(src_list)
    tgt = torch.stack(tgt_list)

    # tgt_y是目标句子去掉第一个token，即去掉<bos>
    tgt_y = tgt[:, 1:]
    # tgt是目标句子去掉最后一个token
    tgt = tgt[:, :-1]

    # 计算本次batch要预测的token数
    n_tokens = (tgt_y != 2).sum()

    # 返回batch后的结果
    return src, tgt, tgt_y, n_tokens


class PositionalEncoding(nn.Module):
    def __init__(self, d_model, dropout, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        # 初始化Shape为(max_len, d_model)的positional encoding
        pe = torch.zeros(max_len, d_model)
        # 初始化一个tensor [[0, 1, 2, 3, ...]]
        position = torch.arange(0, max_len).unsqueeze(1)
        # 这里就是sin和cos括号中的内容，通过e和ln进行了变换
        div_term = torch.exp(
            torch.arange(0, d_model, 2) * -(math.log(10000.0) / d_model)
        )
        # 计算PE(pos, 2i)
        pe[:, 0::2] = torch.sin(position * div_term)
        # 计算PE(pos, 2i+1)
        pe[:, 1::2] = torch.cos(position * div_term)
        # 为了方便计算，在最外面在unsqueeze出一个batch
        pe = pe.unsqueeze(0)
        # 如果一个参数不参与梯度下降，但又希望保存model的时候将其保存下来
        # 这个时候就可以用register_buffer
        self.register_buffer("pe", pe)

    def forward(self, x):
        """
        x 为embedding后的inputs，例如(1,7, 128)，batch size为1,7个单词，单词维度为128
        """
        # 将x和positional encoding相加。
        x = x + self.pe[:, : x.size(1)].requires_grad_(False)
        return self.dropout(x)


# --------------------------
# 模型定义
# --------------------------
class TranslationModel(nn.Module):
    def __init__(self, d_model, src_vocab, tgt_vocab, dropout=0.1):
        super(TranslationModel, self).__init__()
        self.src_embedding = nn.Embedding(len(src_vocab), d_model, padding_idx=2)
        self.tgt_embedding = nn.Embedding(len(tgt_vocab), d_model, padding_idx=2)
        self.positional_encoding = PositionalEncoding(d_model, dropout, max_len=max_length)
        self.transformer = nn.Transformer(
            d_model,
            dropout=dropout,
            batch_first=True,
            nhead=8,
            num_encoder_layers=2,
            num_decoder_layers=2,
            dim_feedforward=128)
        self.predictor = nn.Linear(d_model, len(tgt_vocab))

    def forward(self, src, tgt):
        """原有训练用forward：未改动"""
        tgt_mask = nn.Transformer.generate_square_subsequent_mask(tgt.size()[-1]).to(src.device)
        src_key_padding_mask = TranslationModel.get_key_padding_mask(src).float().to(src.device)
        tgt_key_padding_mask = TranslationModel.get_key_padding_mask(tgt).float().to(src.device)

        src = self.src_embedding(src)
        tgt = self.tgt_embedding(tgt)
        src = self.positional_encoding(src)
        tgt = self.positional_encoding(tgt)

        out = self.transformer(
            src, tgt,
            tgt_mask=tgt_mask,
            src_key_padding_mask=src_key_padding_mask,
            tgt_key_padding_mask=tgt_key_padding_mask
        )
        return out

    @staticmethod
    def get_key_padding_mask(tokens):
        return tokens == 2

    # 新增：自回归生成函数（用于多段翻译推理）
    def generate(self, src, max_gen_len=72):
        """
        单段文本的自回归生成
        :param src: 单段输入张量，shape=(1, seq_len)
        :return: 生成的目标语言token列表（不含<bos>）
        """
        self.eval()  # 推理模式
        with torch.no_grad():
            # 1. 编码器处理src
            src_key_padding_mask = self.get_key_padding_mask(src).float().to(src.device)
            src_emb = self.src_embedding(src)
            src_pe = self.positional_encoding(src_emb)
            memory = self.transformer.encoder(src_pe, src_key_padding_mask=src_key_padding_mask)

            # 2. 初始化解码器输入（仅含<bos>）
            tgt_pred = torch.tensor([[0]], dtype=torch.int64).to(src.device)  # <bos>的索引为0

            # 3. 自回归生成
            for _ in range(max_gen_len):
                # 生成解码器掩码
                tgt_mask = nn.Transformer.generate_square_subsequent_mask(tgt_pred.size(1)).to(src.device)
                tgt_key_padding_mask = self.get_key_padding_mask(tgt_pred).float().to(src.device)

                # 解码器前向计算
                tgt_emb = self.tgt_embedding(tgt_pred)
                tgt_pe = self.positional_encoding(tgt_emb)
                out = self.transformer.decoder(
                    tgt_pe, memory,
                    tgt_mask=tgt_mask,
                    tgt_key_padding_mask=tgt_key_padding_mask,
                    memory_key_padding_mask=src_key_padding_mask
                )

                # 预测下一个token
                logits = self.predictor(out[:, -1, :])
                next_token = sample_top_k(logits, k=5)
                tgt_pred = torch.cat([tgt_pred, next_token], dim=1)

                # 遇到<eos>停止
                if next_token.item() == 1:  # <eos>的索引为1
                    break

            # 4. 处理输出：去掉<bos>和<eos>
            tgt_pred = tgt_pred.squeeze(0).tolist()[1:]  # 去掉batch维度和<bos>
            if 1 in tgt_pred:  # 去掉<eos>及之后的内容
                tgt_pred = tgt_pred[:tgt_pred.index(1)]
            return tgt_pred



# --------------------------
# 多段文本处理工具
# --------------------------
def multi_seg_tokenize(src_multi, src_vocab, max_length):
    """
    将多段文本转换为单段样本列表
    :param src_multi: 多段输入文本，如["I love you.", "He is happy."]
    :param src_vocab: 源语言词典
    :param max_length: 最大序列长度
    :return: 单段样本列表，可直接送入DataLoader
    """
    single_samples = []
    for seg in src_multi:
        # 1. 分词
        tokens = seg.strip().split()  # 示例：空格分词
        # 2. 转为索引（未知词用<unk>，假设<unk>索引为3）
        seg_idx = [src_vocab.get(token, 3) for token in tokens]
        # 3. 截断超长文本（预留<bos>和<eos>的位置）
        if len(seg_idx) > max_length - 2:
            seg_idx = seg_idx[:max_length - 2]
        # 4. 组成样本（tgt用占位符，不影响推理）
        single_samples.append((seg_idx, [0]))  # (src索引, 占位tgt)
    return single_samples


# --------------------------
# 多段翻译推理函数
# --------------------------
def translate_multi_seg(src_multi, model, src_vocab, tgt_vocab, max_length, device):
    """
    多段文本翻译主函数
    :param src_multi: 多段输入文本列表
    :return: 多段翻译结果列表
    """
    # 1. 多段转单段样本
    single_samples = multi_seg_tokenize(src_multi, src_vocab, max_length)
    # 2. 用原有collate_fn批量处理
    loader = DataLoader(
        single_samples,
        batch_size=len(single_samples),  # 一次处理所有段
        collate_fn=collate_fn
    )
    # 3. 模型推理
    model.eval()
    translations = []
    with torch.no_grad():
        for src, _, _, _ in loader:  # 只需要src
            src = src.to(device)
            # 逐段生成翻译
            for i in range(src.shape[0]):
                single_src = src[i].unsqueeze(0)  # 单段输入，shape=(1, seq_len)
                pred_idx = model.generate(single_src, max_gen_len=max_length)
                # 索引转文本
                pred_text = "".join([tgt_vocab.idx_to_token[idx] for idx in pred_idx
                                     if idx != 2])  # 过滤<pad>
                translations.append(pred_text)
    return translations

best_model_path = "D:/homework/homework/Summer/files/model_best.pt"

def sample_top_k(logits, k=5):
    topk_probs, topk_indices = torch.topk(torch.softmax(logits, dim=-1), k)
    idx = torch.multinomial(topk_probs, 1)  # 按概率抽样
    return topk_indices.gather(-1, idx)


# 2. 定义翻译函数
def translate(src: str):
    """
    :param src: 英文句子，例如 "I like machine learning."
    :return: 翻译后的句子，例如：”我喜欢机器学习“
    """
    # 英文句子分词 → 转词典index → 增加<BOS>(<s>, 0)和<EOS>(</s>, 1)
    src_tok = en_tokenizer(src)
    src_indices = [0] + en_vocab(src_tok) + [1]  # 拼接特殊符号
    # 转为tensor并增加batch维度（模型输入要求batch_first=True）
    src_tensor = torch.tensor(src_indices).unsqueeze(0).to(device)

    # 初始化目标语言输入：仅包含<BOS>（起始符号）
    tgt_tensor = torch.tensor([[0]]).to(device)  # shape: (1, 1)

    # 逐词预测：直到出现<EOS>或达到最大长度
    max_gen_len = min(max_length, len(src_indices) + 4)  # 限制生成长度，避免无限循环
    for _ in range(max_gen_len):
        # 模型前向传播（评估模式下无需计算梯度）
        with torch.no_grad():
            out = infer_model(src_tensor, tgt_tensor)
            # 取最后一个token的预测结果（因为是自回归生成）
            pred_logits = infer_model.predictor(out[:, -1])  # shape: (1, 中文词典大小)
            # 选择概率最大的token索引
            pred_token_idx = sample_top_k(pred_logits, k=5).squeeze(1)

        # 将预测的token拼接到目标序列中
        tgt_tensor = torch.concat([tgt_tensor, pred_token_idx.unsqueeze(0)], dim=1)

        # 若预测到<EOS>（索引1），停止生成
        if pred_token_idx.item() == 1:
            break

    # 将预测的token索引转为中文文本（清理特殊符号）
    tgt_tokens = zh_vocab.lookup_tokens(tgt_tensor.squeeze().tolist())
    # 移除<BOS>、<EOS>、<PAD>等特殊符号
    translated_text = ''.join([tok for tok in tgt_tokens
                               if tok not in ["<s>", "</s>", "<pad>"]])
    return translated_text

@app.post("/en-zh")
def Translate(item:TranslationRequest):
    text=translate(item.source_text)
    return text

if __name__ == "__main__":
    uvicorn.run(app,host="127.0.0.1",port=8867)