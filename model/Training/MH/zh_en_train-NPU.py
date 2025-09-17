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

HAS_MATPLOTLIB = True

# 参数解析
parser = argparse.ArgumentParser(description='Chinese-English Translation Training')
parser.add_argument('--data_path', type=str,
                    default='/opt/dpcvol/datasets/3139836729765054892/wmt_zh_en_training_corpus.csv',
                    help='Path to the training data CSV file')
parser.add_argument('--output_dir', type=str, default='/home/work/user-job-dir/app/output/models',
                    help='Directory to save the trained models')
parser.add_argument('--log_dir', type=str, default='/home/work/user-job-dir/app/output/models/TRS/log',
                    help='Directory to save training logs')
parser.add_argument('--vocab_dir', type=str, default='/home/work/user-job-dir/app/output/models/vocab',
                    help='Directory to save vocabulary files')
parser.add_argument('--batch_size', type=int, default=16, help='Batch size for training')
parser.add_argument('--epochs', type=int, default=20, help='Number of training epochs')
parser.add_argument('--d_model', type=int, default=256, help='Model dimension')
parser.add_argument('--max_length', type=int, default=64, help='Maximum sequence length')
parser.add_argument('--learning_rate', type=float, default=0.0001, help='Learning rate')
parser.add_argument('--save_interval', type=int, default=5, help='Save model every n epochs')
parser.add_argument('--log_interval', type=int, default=100, help='Log training progress every n steps')
parser.add_argument('--num_layers', type=int, default=6, help='Number of transformer layers')
args = parser.parse_args()

ms.set_seed(42)

context.set_context(
    mode=context.PYNATIVE_MODE,
    device_target="Ascend",
    max_device_memory="6GB"
)

logger = logging.getLogger("TranslationDataset")

PAD_TOKEN = "<pad>"
BOS_TOKEN = "<s>"
EOS_TOKEN = "</s>"
UNK_TOKEN = "<unk>"
SPECIAL_TOKENS = [BOS_TOKEN, EOS_TOKEN, PAD_TOKEN, UNK_TOKEN]


# 设置日志
def setup_logging(log_dir):
    """设置日志配置"""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"training_{timestamp}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger("TranslationTraining")
    logger.info(f"Logging to file: {log_file}")

    return logger, log_file


logger, log_file = setup_logging(args.log_dir)


class LossRecorder:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        self.epoch_losses = []
        self.epoch_accuracies = []
        self.step_losses = []
        self.step_accuracies = []

        self.loss_csv_path = os.path.join(log_dir, "loss_records.csv")
        with open(self.loss_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['epoch', 'step', 'loss', 'accuracy', 'timestamp'])

        logger.info(f"Loss records will be saved to: {self.loss_csv_path}")

    def record_step(self, epoch, step, loss, accuracy):
        """记录每一步的损失"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.step_losses.append((epoch, step, loss, accuracy, timestamp))

        with open(self.loss_csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([epoch, step, loss, accuracy, timestamp])

    def record_epoch(self, epoch, avg_loss, avg_accuracy):
        """记录每个epoch的平均损失"""
        self.epoch_losses.append((epoch, avg_loss))
        self.epoch_accuracies.append((epoch, avg_accuracy))
        logger.info(f"Epoch {epoch} completed, Average Loss: {avg_loss:.6f}, Average Accuracy: {avg_accuracy:.4f}")

    def plot_loss_curve(self):
        """绘制损失曲线"""
        if not HAS_MATPLOTLIB or not self.epoch_losses:
            logger.warning("Cannot plot loss curve: matplotlib not available or no data")
            return

        try:
            plt.figure(figsize=(12, 6))

            epochs, losses = zip(*self.epoch_losses)
            plt.subplot(1, 2, 1)
            plt.plot(epochs, losses, 'b-', label='Epoch Loss')
            plt.xlabel('Epoch')
            plt.ylabel('Loss')
            plt.title('Training Loss per Epoch')
            plt.grid(True)
            plt.legend()

            _, accuracies = zip(*self.epoch_accuracies)
            plt.subplot(1, 2, 2)
            plt.plot(epochs, accuracies, 'g-', label='Epoch Accuracy')
            plt.xlabel('Epoch')
            plt.ylabel('Accuracy')
            plt.title('Training Accuracy per Epoch')
            plt.grid(True)
            plt.legend()

            plt.tight_layout()
            loss_plot_path = os.path.join(self.log_dir, "loss_accuracy_curve.png")
            plt.savefig(loss_plot_path)
            plt.close()

            logger.info(f"Loss and accuracy curve saved to: {loss_plot_path}")

        except Exception as e:
            logger.error(f"Failed to plot loss and accuracy curve: {str(e)}")

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

        self.src_embedding = nn.Embedding(
            src_vocab_size, d_model, padding_idx=SPECIAL_TOKENS.index(PAD_TOKEN)
        )
        self.tgt_embedding = nn.Embedding(
            tgt_vocab_size, d_model, padding_idx=SPECIAL_TOKENS.index(PAD_TOKEN)
        )

        self.positional_encoding = PositionalEncoding(d_model, dropout, max_len)

        self.transformer = nn.Transformer(
            d_model=d_model,
            nhead=8,
            num_encoder_layers=args.num_layers,
            num_decoder_layers=args.num_layers,
            dim_feedforward=1024,
            dropout=dropout,
            batch_first=True
        )

        self.predictor = nn.Dense(d_model, tgt_vocab_size)
        self.tgt_mask_full = self.generate_square_subsequent_mask(max_len)

    def generate_square_subsequent_mask(self, size):
        mask = np.triu(np.ones((size, size)), k=1).astype(np.bool_)
        return Tensor(mask, dtype=ms.bool_)

    def construct(self, src, tgt):
        pad_id = SPECIAL_TOKENS.index(PAD_TOKEN)
        src_key_padding_mask = (src == pad_id)
        tgt_key_padding_mask = (tgt == pad_id)

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
    def __init__(self, data_path, max_length=64, use_mindrecord=False, mindrecord_path=None):
        self.data_path = data_path
        self.max_length = max_length
        self.use_mindrecord = use_mindrecord
        self.mindrecord_path = mindrecord_path
        self.data = []
        self.zh_token_to_id = {}
        self.en_token_to_id = {}
        self.zh_vocab_size = 0
        self.en_vocab_size = 0

        if use_mindrecord:
            if not mindrecord_path:
                raise ValueError("MindRecord path must be provided if use_mindrecord is True.")
            self._load_from_mindrecord()
        else:
            self._load_data()

    def _load_data(self):
        logger.info(f"Loading dataset from {self.data_path}")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:]
            for i, line in enumerate(lines):
                parts = line.strip().split(',', 1)
                if len(parts) == 2:
                    chinese, english = parts
                    self.data.append((chinese.strip(), english.strip()))

                if i >= 500000:
                    break
                if i % 10000 == 0 and i > 0:
                    logger.info(f"Processed {i} lines")

        logger.info(f"Dataset loaded with {len(self.data)} samples")
        self.build_vocabularies()

    def _load_from_mindrecord(self):
        """从MindRecord文件中加载数据"""
        logger.info(f"Loading dataset from MindRecord file: {self.mindrecord_path}")
        from mindspore.mindrecord import FileReader
        reader = FileReader(self.mindrecord_path)
        for record in reader.get_next():
            zh_text, en_text = record['src'], record['tgt']
            self.data.append((zh_text, en_text))

        logger.info(f"Dataset loaded from MindRecord with {len(self.data)} samples")
        self.build_vocabularies()

    def save_vocabularies(self, vocab_dir):
        """保存词汇表到指定目录（JSON格式）"""
        os.makedirs(vocab_dir, exist_ok=True)

        zh_vocab_path = os.path.join(vocab_dir, "zh_vocab.json")
        zh_vocab_data = {
            "vocab": self.zh_vocab,
            "token_to_id": self.zh_token_to_id,
            "vocab_size": self.zh_vocab_size,
            "special_tokens": {
                "PAD_TOKEN": PAD_TOKEN,
                "BOS_TOKEN": BOS_TOKEN,
                "EOS_TOKEN": EOS_TOKEN,
                "UNK_TOKEN": UNK_TOKEN,
                "PAD_ID": SPECIAL_TOKENS.index(PAD_TOKEN),
                "BOS_ID": SPECIAL_TOKENS.index(BOS_TOKEN),
                "EOS_ID": SPECIAL_TOKENS.index(EOS_TOKEN),
                "UNK_ID": SPECIAL_TOKENS.index(UNK_TOKEN)
            }
        }
        with open(zh_vocab_path, 'w', encoding='utf-8') as f:
            json.dump(zh_vocab_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Chinese vocabulary saved to: {zh_vocab_path}")

        # 保存英文词汇表（JSON格式）
        en_vocab_path = os.path.join(vocab_dir, "en_vocab.json")
        en_vocab_data = {
            "vocab": self.en_vocab,
            "token_to_id": self.en_token_to_id,
            "vocab_size": self.en_vocab_size,
            "special_tokens": {
                "PAD_TOKEN": PAD_TOKEN,
                "BOS_TOKEN": BOS_TOKEN,
                "EOS_TOKEN": EOS_TOKEN,
                "UNK_TOKEN": UNK_TOKEN,
                "PAD_ID": SPECIAL_TOKENS.index(PAD_TOKEN),
                "BOS_ID": SPECIAL_TOKENS.index(BOS_TOKEN),
                "EOS_ID": SPECIAL_TOKENS.index(EOS_TOKEN),
                "UNK_ID": SPECIAL_TOKENS.index(UNK_TOKEN)
            }
        }
        with open(en_vocab_path, 'w', encoding='utf-8') as f:
            json.dump(en_vocab_data, f, ensure_ascii=False, indent=4)
        logger.info(f"English vocabulary saved to: {en_vocab_path}")

        vocab_stats_path = os.path.join(vocab_dir, "vocab_statistics.json")
        vocab_stats = {
            "timestamp": datetime.now().isoformat(),
            "source_language": "Chinese",
            "target_language": "English",
            "source_vocab_size": self.zh_vocab_size,
            "target_vocab_size": self.en_vocab_size,
            "special_tokens": SPECIAL_TOKENS,
            "max_sequence_length": self.max_length,
            "dataset_size": len(self.data)
        }
        with open(vocab_stats_path, 'w', encoding='utf-8') as f:
            json.dump(vocab_stats, f, ensure_ascii=False, indent=4)
        logger.info(f"Vocabulary statistics saved to: {vocab_stats_path}")

    def save_to_mindrecord(self):
        """将数据保存为MindRecord格式"""
        if not self.mindrecord_path:
            raise ValueError("MindRecord path must be specified.")

        writer = FileWriter(self.mindrecord_path, num_shards=1)
        writer.add_schema({
            "src": {"type": "int32", "shape": [-1]},
            "tgt": {"type": "int32", "shape": [-1]}
        })

        for zh, en in self.data:
            zh_tokens = [self.zh_token_to_id[BOS_TOKEN]] + self.tokenize_zh(zh) + [self.zh_token_to_id[EOS_TOKEN]]
            en_tokens = [self.en_token_to_id[BOS_TOKEN]] + self.tokenize_en(en) + [self.en_token_to_id[EOS_TOKEN]]

            zh_tokens = self.pad_or_truncate(zh_tokens)
            en_tokens = self.pad_or_truncate(en_tokens)

            data = {
                "src": np.array(zh_tokens, dtype=np.int32),
                "tgt": np.array(en_tokens, dtype=np.int32)
            }
            writer.write_raw_data([data])

        writer.commit()
        logger.info(f"Data saved to {self.mindrecord_path}")

    def build_vocabularies(self):
        logger.info("Building vocabularies...")
        zh_chars = set()
        en_words = set()

        for zh, en in self.data:
            zh_chars.update(list(zh))
            en_words.update(en.lower().split())

        self.zh_vocab = SPECIAL_TOKENS + sorted(list(zh_chars))
        self.en_vocab = SPECIAL_TOKENS + sorted(list(en_words))

        self.zh_vocab_size = len(self.zh_vocab)
        self.en_vocab_size = len(self.en_vocab)

        self.zh_token_to_id = {token: idx for idx, token in enumerate(self.zh_vocab)}
        self.en_token_to_id = {token: idx for idx, token in enumerate(self.en_vocab)}

        logger.info(f"Chinese vocabulary size: {self.zh_vocab_size}")
        logger.info(f"English vocabulary size: {self.en_vocab_size}")

        self.save_vocabularies(args.vocab_dir)

    def tokenize_zh(self, text):
        return [self.zh_token_to_id.get(char, self.zh_token_to_id[UNK_TOKEN]) for char in text]

    def tokenize_en(self, text):
        return [self.en_token_to_id.get(token, self.en_token_to_id[UNK_TOKEN]) for token in text.lower().split()]

    def pad_or_truncate(self, tokens):
        if len(tokens) > self.max_length:
            return tokens[:self.max_length]
        else:
            return tokens + [self.zh_token_to_id[PAD_TOKEN]] * (self.max_length - len(tokens))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        zh_text, en_text = self.data[idx]

        zh_tokens = [self.zh_token_to_id[BOS_TOKEN]] + self.tokenize_zh(zh_text) + [self.zh_token_to_id[EOS_TOKEN]]
        en_tokens = [self.en_token_to_id[BOS_TOKEN]] + self.tokenize_en(en_text) + [self.en_token_to_id[EOS_TOKEN]]

        zh_tokens = self.pad_or_truncate(zh_tokens)
        en_tokens = self.pad_or_truncate(en_tokens)

        return np.array(zh_tokens, dtype=np.int32), np.array(en_tokens, dtype=np.int32)


def create_dataset(data_path, batch_size=32, max_length=64, use_mindrecord=False, mindrecord_path=None):
    dataset = TranslationDataset(data_path, max_length, use_mindrecord, mindrecord_path)
    mindspore_dataset = GeneratorDataset(dataset, column_names=["src", "tgt"], shuffle=True, num_parallel_workers=4)
    mindspore_dataset = mindspore_dataset.batch(batch_size)
    return mindspore_dataset, dataset.zh_vocab_size, dataset.en_vocab_size


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

    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)

    # 创建数据集
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
        epoch_accuracy = 0
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

            predicted_ids = np.argmax(loss_value, axis=-1)
            accuracy = np.mean(np.equal(predicted_ids, labels.asnumpy()))
            epoch_accuracy += accuracy

            loss_recorder.record_step(epoch + 1, step, loss_value, accuracy)

            progress_bar.set_postfix(loss=loss_value, accuracy=accuracy)
            progress_bar.update(1)

        progress_bar.close()

        avg_loss = epoch_loss / step
        avg_accuracy = epoch_accuracy / step
        epoch_time = time.time() - epoch_start_time

        loss_recorder.record_epoch(epoch + 1, avg_loss, avg_accuracy)

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
