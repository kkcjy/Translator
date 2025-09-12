import argparse
import os
from tqdm import tqdm
import math
import numpy as np
import mindspore as ms
import mindspore.nn as nn
import mindspore.ops as ops
from mindspore import Tensor, Parameter
from mindspore.common.initializer import initializer, XavierUniform
from mindspore.dataset import GeneratorDataset, text
from mindspore.train.callback import Callback, LossMonitor, TimeMonitor
from mindspore.train import Model
from mindspore.mindrecord import FileWriter
import logging
import time
import mindspore.dataset as ds
import mindspore.communication as comm
from mindspore import context
from datetime import datetime
import json
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Chinese-English Translation Training')
parser.add_argument('--data_path', type=str, default='/opt/dpcvol/datasets/3139836729765054892/data.csv',help='Path to the training data CSV file')
parser.add_argument('--output_dir', type=str, default='/home/work/user-job-dir/app/output/models',help='Directory to save the trained models')
parser.add_argument('--log_dir', type=str, default='/home/work/user-job-dir/app/output/models/TRS/log',                  help='Directory to save training logs')
parser.add_argument('--batch_size', type=int, default=32, help='Batch size for training')
parser.add_argument('--epochs', type=int, default=10, help='Number of training epochs')
parser.add_argument('--d_model', type=int, default=256, help='Model dimension')
parser.add_argument('--max_length', type=int, default=64, help='Maximum sequence length')
parser.add_argument('--learning_rate', type=float, default=0.0001, help='Learning rate')
parser.add_argument('--save_interval', type=int, default=5, help='Save model every n epochs')
parser.add_argument('--log_interval', type=int, default=100, help='Log training progress every n steps')
parser.add_argument('--num_layers', type=int, default=4, help='Number of transformer layers')
args = parser.parse_args()

ms.set_seed(42)
context.set_context(mode=context.PYNATIVE_MODE,device_target="Ascend",max_device_memory="6GB")

PAD_TOKEN = "<pad>"
BOS_TOKEN = "<s>"
EOS_TOKEN = "</s>"
UNK_TOKEN = "<unk>"
SPECIAL_TOKENS = [BOS_TOKEN, EOS_TOKEN, PAD_TOKEN, UNK_TOKEN]


# 设置日志
def setup_logging(log_dir):
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"training_{timestamp}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file),logging.StreamHandler()]
    )

    logger = logging.getLogger("TranslationTraining")
    logger.info(f"Logging to file: {log_file}")
    return logger, log_file

logger, log_file = setup_logging(args.log_dir)

class LossRecorder:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        self.epoch_losses = []
        self.step_losses = []
        self.loss_csv_path = os.path.join(log_dir, "loss_records.csv")
        with open(self.loss_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['epoch', 'step', 'loss', 'timestamp'])
        logger.info(f"Loss records will be saved to: {self.loss_csv_path}")

    def record_step(self, epoch, step, loss):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.step_losses.append((epoch, step, loss, timestamp))
        with open(self.loss_csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([epoch, step, loss, timestamp])

    def record_epoch(self, epoch, avg_loss):
        self.epoch_losses.append((epoch, avg_loss))
        logger.info(f"Epoch {epoch} completed, Average Loss: {avg_loss:.6f}")

    def plot_loss_curve(self):
        if not self.epoch_losses:
            logger.warning("Cannot plot loss curve: matplotlib not available or no data")
            return
        plt.figure(figsize=(12, 6))
        epochs, losses = zip(*self.epoch_losses)
        plt.subplot(1, 2, 1)
        plt.plot(epochs, losses, 'b-', label='Epoch Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('Training Loss per Epoch')
        plt.grid(True)
        plt.legend()

        if self.step_losses:
            steps = range(0, len(self.step_losses), max(1, len(self.step_losses) // 100))
            sampled_losses = [self.step_losses[i][2] for i in steps]
            plt.subplot(1, 2, 2)
            plt.plot(steps, sampled_losses, 'r-', alpha=0.7, label='Step Loss')
            plt.xlabel('Step')
            plt.ylabel('Loss')
            plt.title('Training Loss per Step (Sampled)')
            plt.grid(True)
            plt.legend()

        plt.tight_layout()
        loss_plot_path = os.path.join(self.log_dir, "loss_curve.png")
        plt.savefig(loss_plot_path)
        plt.close()

        logger.info(f"Loss curve saved to: {loss_plot_path}")

    def save_summary(self, total_time, final_loss):
        summary_path = os.path.join(self.log_dir, "training_summary.json")
        summary = {
            "total_training_time": total_time,
            "final_loss": final_loss,
            "total_epochs": len(self.epoch_losses),
            "total_steps": len(self.step_losses),
            "average_epoch_loss": sum(loss for _, loss in self.epoch_losses) / len(
                self.epoch_losses) if self.epoch_losses else 0,
            "start_time": self.step_losses[0][3] if self.step_losses else "",
            "end_time": self.step_losses[-1][3] if self.step_losses else "",
        }

        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=4)

        logger.info(f"Training summary saved to: {summary_path}")
        logger.info(f"Training completed in {total_time:.2f} seconds")
        logger.info(f"Final loss: {final_loss:.6f}")

loss_recorder = LossRecorder(args.log_dir)


class PositionalEncoding(nn.Cell):
    def __init__(self, d_model, dropout, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = np.zeros((max_len, d_model))
        position = np.arange(0, max_len).reshape(-1, 1)
        div_term = np.exp(np.arange(0, d_model, 2) * -(math.log(10000.0) / d_model))

        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)

        self.pe = Tensor(pe, dtype=ms.float32).unsqueeze(0)

    def construct(self, x):
        x = x + self.pe[:, :x.shape[1]]
        return self.dropout(x)


class TranslationModel(nn.Cell):
    def __init__(self, src_vocab_size, tgt_vocab_size, d_model, max_len, dropout=0.1):
        super(TranslationModel, self).__init__()
        self.d_model = d_model
        self.max_len = max_len

        # 嵌入层
        self.src_embedding = nn.Embedding(
            src_vocab_size, d_model, padding_idx=SPECIAL_TOKENS.index(PAD_TOKEN)
        )
        self.tgt_embedding = nn.Embedding(
            tgt_vocab_size, d_model, padding_idx=SPECIAL_TOKENS.index(PAD_TOKEN)
        )

        # 位置编码
        self.positional_encoding = PositionalEncoding(d_model, dropout, max_len)

        # Transformer
        self.transformer = nn.Transformer(
            d_model=d_model,
            nhead=8,
            num_encoder_layers=args.num_layers,
            num_decoder_layers=args.num_layers,
            dim_feedforward=1024,
            dropout=dropout,
            batch_first=True
        )

        # 输出层
        self.predictor = nn.Dense(d_model, tgt_vocab_size)

        # 预生成最大长度的mask
        self.tgt_mask_full = self.generate_square_subsequent_mask(max_len)

    def generate_square_subsequent_mask(self, size):
        mask = np.triu(np.ones((size, size)), k=1).astype(np.bool_)
        return Tensor(mask, dtype=ms.bool_)

    def construct(self, src, tgt):
        pad_id = SPECIAL_TOKENS.index(PAD_TOKEN)

        src_key_padding_mask = (src == pad_id)  # (B, src_len)
        tgt_key_padding_mask = (tgt == pad_id)  # (B, tgt_len)

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


class TranslationDataset:
    def __init__(self, data_path, max_length=64):
        self.data = []
        self.max_length = max_length

        logger.info(f"Loading dataset from {data_path}")

        with open(data_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:]  # 跳过标题行

            for i, line in enumerate(lines):
                parts = line.strip().split(',', 1)
                if len(parts) == 2:
                    chinese, english = parts
                    self.data.append((chinese.strip(), english.strip()))
                if i >= 100000:  # 只使用前100,000个样本
                    break

                if i % 10000 == 0 and i > 0:
                    logger.info(f"Processed {i} lines")

        logger.info(f"Dataset loaded with {len(self.data)} samples")

        self.build_vocabularies()

    def build_vocabularies(self):
        logger.info("Building vocabularies...")

        zh_chars = set()
        for zh, _ in self.data:
            zh_chars.update(list(zh))

        en_words = set()
        for _, en in self.data:
            words = en.lower().split()
            en_words.update(words)

        self.zh_vocab = SPECIAL_TOKENS + sorted(list(zh_chars))
        self.en_vocab = SPECIAL_TOKENS + sorted(list(en_words))

        self.zh_vocab_size = len(self.zh_vocab)
        self.en_vocab_size = len(self.en_vocab)

        self.zh_token_to_id = {token: idx for idx, token in enumerate(self.zh_vocab)}
        self.en_token_to_id = {token: idx for idx, token in enumerate(self.en_vocab)}

        logger.info(f"Chinese vocabulary size: {self.zh_vocab_size}")
        logger.info(f"English vocabulary size: {self.en_vocab_size}")

    def tokenize_zh(self, text):
        return [self.zh_token_to_id.get(char, self.zh_token_to_id[UNK_TOKEN]) for char in text]

    def tokenize_en(self, text):
        tokens = text.lower().split()
        return [self.en_token_to_id.get(token, self.en_token_to_id[UNK_TOKEN]) for token in tokens]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        zh_text, en_text = self.data[idx]

        zh_tokens = [self.zh_token_to_id[BOS_TOKEN]] + self.tokenize_zh(zh_text) + [self.zh_token_to_id[EOS_TOKEN]]
        en_tokens = [self.en_token_to_id[BOS_TOKEN]] + self.tokenize_en(en_text) + [self.en_token_to_id[EOS_TOKEN]]

        zh_tokens = self.pad_or_truncate(zh_tokens)
        en_tokens = self.pad_or_truncate(en_tokens)

        return np.array(zh_tokens, dtype=np.int32), np.array(en_tokens, dtype=np.int32)

    def pad_or_truncate(self, tokens):
        if len(tokens) > self.max_length:
            return tokens[:self.max_length]
        else:
            return tokens + [self.zh_token_to_id[PAD_TOKEN]] * (self.max_length - len(tokens))


class TranslationLoss(nn.Cell):
    def __init__(self):
        super(TranslationLoss, self).__init__()
        self.cross_entropy = nn.SoftmaxCrossEntropyWithLogits(sparse=True, reduction='none')
        self.cast = ops.Cast()
        self.reshape = ops.Reshape()

    def construct(self, logits, labels):
        labels = self.cast(labels, ms.int32)
        batch_size, seq_length, vocab_size = logits.shape

        logits_reshaped = self.reshape(logits, (-1, vocab_size))
        labels_reshaped = self.reshape(labels, (-1,))

        mask = (labels_reshaped != SPECIAL_TOKENS.index(PAD_TOKEN))

        loss = self.cross_entropy(logits_reshaped, labels_reshaped)
        loss = loss * mask
        result = loss.sum() / mask.sum()
        return result


def create_dataset(data_path, batch_size=32, max_length=64):
    dataset = TranslationDataset(data_path, max_length)
    mindspore_dataset = GeneratorDataset(dataset, column_names=["src", "tgt"], shuffle=True)
    mindspore_dataset = mindspore_dataset.batch(batch_size)
    return mindspore_dataset, dataset.zh_vocab_size, dataset.en_vocab_size


class Seq2SeqWithLoss(nn.Cell):
    def __init__(self, network, loss_fn):
        super(Seq2SeqWithLoss, self).__init__()
        self.network = network
        self.loss_fn = loss_fn

    def construct(self, *inputs):
        if len(inputs) == 3:
            src, tgt, labels = inputs
        elif len(inputs) == 4:
            src, tgt, labels, _ = inputs
        elif len(inputs) == 2:
            first, second = inputs
            if isinstance(first, tuple) or isinstance(first, list):
                try:
                    src, tgt = first
                    labels = second
                except Exception:
                    raise TypeError(
                        "Unexpected input format for Seq2SeqWithLoss: first element is tuple but cannot unpack to (src,tgt).")
            else:
                raise TypeError("Seq2SeqWithLoss expects (src, tgt, labels), got 2 non-tuple arguments.")
        elif len(inputs) == 1:
            single = inputs[0]
            if isinstance(single, (tuple, list)) and len(single) == 3:
                src, tgt, labels = single
            elif isinstance(single, (tuple, list)) and len(single) == 2:
                src, tgt = single
                raise TypeError("Seq2SeqWithLoss received (src, tgt) only — labels missing.")
            else:
                raise TypeError("Seq2SeqWithLoss got unsupported single argument type/shape.")
        else:
            raise TypeError(
                f"Seq2SeqWithLoss received unexpected number of args: {len(inputs)}. Expected 2-4 (src, tgt, labels[, sens]).")

        logits = self.network(src, tgt)
        loss = self.loss_fn(logits, labels)
        return loss


def train():
    logger.info("Starting translation model training")
    logger.info(f"Arguments: {args}")

    os.makedirs(args.output_dir, exist_ok=True)

    logger.info("Creating dataset...")
    dataset, src_vocab_size, tgt_vocab_size = create_dataset(
        args.data_path, args.batch_size, args.max_length
    )

    logger.info(f"Source vocabulary size: {src_vocab_size}")
    logger.info(f"Target vocabulary size: {tgt_vocab_size}")
    logger.info(f"Model dimension: {args.d_model}")
    logger.info(f"Max sequence length: {args.max_length}")
    logger.info(f"Number of transformer layers: {args.num_layers}")

    logger.info("Initializing model...")
    model = TranslationModel(src_vocab_size, tgt_vocab_size, args.d_model, args.max_length)

    loss_fn = TranslationLoss()
    optimizer = nn.Adam(model.trainable_params(), learning_rate=args.learning_rate)

    net_with_loss = Seq2SeqWithLoss(model, loss_fn)
    train_net = nn.TrainOneStepCell(net_with_loss, optimizer)
    train_net.set_train()

    logger.info(f"Starting training for {args.epochs} epochs")
    start_time = time.time()

    dataset_size = dataset.get_dataset_size()

    for epoch in range(args.epochs):
        epoch_loss = 0
        step = 0
        epoch_start_time = time.time()

        progress_bar = tqdm(total=dataset_size, desc=f"Epoch {epoch + 1}/{args.epochs}")

        for data in dataset.create_dict_iterator():
            src = data['src']
            tgt = data['tgt']

            decoder_input = tgt[:, :-1]
            labels = tgt[:, 1:]

            loss = train_net(src, decoder_input, labels)
            loss_value = loss.asnumpy()
            epoch_loss += loss_value
            step += 1

            loss_recorder.record_step(epoch + 1, step, loss_value)

            progress_bar.set_postfix(loss=loss_value)
            progress_bar.update(1)

        progress_bar.close()

        avg_loss = epoch_loss / step
        epoch_time = time.time() - epoch_start_time

        loss_recorder.record_epoch(epoch + 1, avg_loss)

        if (epoch + 1) % args.save_interval == 0:
            model_path = os.path.join(args.output_dir, f"translation_model_epoch_{epoch + 1}.ckpt")
            ms.save_checkpoint(model, model_path)
            logger.info(f"Model saved at {model_path}")

    total_time = time.time() - start_time
    final_loss = avg_loss

    final_model_path = os.path.join(args.output_dir, "translation_model_final.ckpt")
    ms.save_checkpoint(model, final_model_path)
    logger.info(f"Final model saved at {final_model_path}")

    config_path = os.path.join(args.output_dir, "training_config.txt")
    with open(config_path, 'w') as f:
        f.write(f"Training completed at: {datetime.now()}\n")
        f.write(f"Total training time: {total_time:.2f}s\n")
        f.write(f"Epochs: {args.epochs}\n")
        f.write(f"Batch size: {args.batch_size}\n")
        f.write(f"Learning rate: {args.learning_rate}\n")
        f.write(f"Model dimension: {args.d_model}\n")
        f.write(f"Max sequence length: {args.max_length}\n")
        f.write(f"Source vocabulary size: {src_vocab_size}\n")
        f.write(f"Target vocabulary size: {tgt_vocab_size}\n")
        f.write(f"Final loss: {final_loss:.6f}\n")

    logger.info(f"Training configuration saved at {config_path}")

    loss_recorder.plot_loss_curve()
    loss_recorder.save_summary(total_time, final_loss)

    return final_loss


if __name__ == "__main__":
    final_loss = train()
    logger.info(f"Training completed successfully with final loss: {final_loss:.6f}")
