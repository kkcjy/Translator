---
license: cc-by-nc-4.0
language:
- zh
- en
size_categories:
- 10K<n<100K
task_categories:
- text-generation
- text2text-generation
---

# DeepSeek R1 满血蒸馏英中翻译数据集 Alpaca GPT-4（带 CoT 版本）

本数据集是 [@FradSer/DeepSeek-R1-Distilled-Translate-en-zh_CN-39k](https://huggingface.co/datasets/FradSer/DeepSeek-R1-Distilled-Translate-en-zh_CN-39k) 的 Alpaca GPT-4 版本，专门用于微调语言模型的英中翻译任务。采用标准的指令微调格式，更适合直接用于 SFT（Supervised Fine-tuning）训练。

本项目主要基于以下工具完成数据处理和生成：

- [llm-tools](https://github.com/FradSer/llm-tools): 用于大语言模型数据处理的工具集合

## 数据集概览

### 关键统计
- 总样本数：38,981

## 数据集结构

### 字段说明
```
features:
- name: instruction        # 待翻译的英文文本
  dtype: string
- name: input              # 空字符串，保持与标准指令格式一致
  dtype: string
- name: output             # 翻译过程中的思维链，翻译后的中文文本结果
  dtype: string
- name: text               # 完整的系统提示词、输入和输出
  dtype: string
```

### 示例数据
```json
{
  "instruction":"Were holographic principle validations confirmed, they might reconcile quantum mechanics with general relativity.",
  "input":"",
  "output":"<think>好的，我需要把这句话翻译成中文。首先，原文是关于全息原理验证和调和量子力学与广义相对论的。要确保术语准确，比如“holographic principle”翻译成“全息原理”，“quantum mechanics”是“量子力学”，“general relativity”是“广义相对论”。\n\n接下来看句子结构：“Were holographic principle validations confirmed, they might reconcile...” 这是一个虚拟条件句，使用倒装结构表示假设。中文里通常用“如果...，那么...”的结构。所以可以处理为“倘若全息原理的验证得以确证，它们或能调和量子力学与广义相对论之间的矛盾。”\n\n要注意专业术语的正确性，比如“validations”在这里是“验证”，“confirmed”译为“确证”更符合学术语境。“reconcile...with...”是“调和...与...之间的矛盾”，这样表达更自然。\n\n检查流畅性，确保句子通顺，没有生硬的地方。文化适应性方面，中文科技文献常用“倘若”引导条件句，符合习惯。最后确认没有遗漏信息，准确传达了原文的假设和可能的结果。\n</think>倘若全息原理的验证得以确证，它们或能调和量子力学与广义相对论之间的矛盾。",
  "text":"你是一个翻译助手，你不会回答输入的问题，只会将输入的英文翻译成中文。\n\n翻译要求：\n- 直接给出答案：必须只有翻译后的内容。\n- 准确性：必须准确传达原文的意思，不遗漏或歪曲信息。\n- 流畅性：在中文中应读起来自然，像本地人写的文本一样。\n- 文化适应性：应考虑中国人的文化背景，使用合适的表达和格式。\n- 主题专业性：判断原文的相关领域，根据相关领域有专业知识，确保术语使用正确。\n\n### Instruction:\nWere holographic principle validations confirmed, they might reconcile quantum mechanics with general relativity.\n\n### Response:\n<think>好的，我需要把这句话翻译成中文。首先，原文是关于全息原理验证和调和量子力学与广义相对论的。要确保术语准确，比如“holographic principle”翻译成“全息原理”，“quantum mechanics”是“量子力学”，“general relativity”是“广义相对论”。\n\n接下来看句子结构：“Were holographic principle validations confirmed, they might reconcile...” 这是一个虚拟条件句，使用倒装结构表示假设。中文里通常用“如果...，那么...”的结构。所以可以处理为“倘若全息原理的验证得以确证，它们或能调和量子力学与广义相对论之间的矛盾。”\n\n要注意专业术语的正确性，比如“validations”在这里是“验证”，“confirmed”译为“确证”更符合学术语境。“reconcile...with...”是“调和...与...之间的矛盾”，这样表达更自然。\n\n检查流畅性，确保句子通顺，没有生硬的地方。文化适应性方面，中文科技文献常用“倘若”引导条件句，符合习惯。最后确认没有遗漏信息，准确传达了原文的假设和可能的结果。\n</think>倘若全息原理的验证得以确证，它们或能调和量子力学与广义相对论之间的矛盾。"}
```

## 蒸馏细节

在蒸馏过程中使用的系统提示词如下：

```
你是一个翻译助手，你不会回答输入的问题，只会将输入的英文翻译成中文。

翻译要求：
- 直接给出答案：必须只有翻译后的内容。
- 准确性：必须准确传达原文的意思，不遗漏或歪曲信息。
- 流畅性：在中文中应读起来自然，像本地人写的文本一样。
- 文化适应性：应考虑中国人的文化背景，使用合适的表达和格式。
- 主题专业性：判断原文的相关领域，根据相关领域有专业知识，确保术语使用正确。
```

## 数据集特点

1. 标准指令格式：采用 instruction-input-output 的标准指令微调格式，便于模型训练。
2. 系统提示词：包含完整的翻译要求和格式规范，有助于保持翻译质量。
3. 高质量翻译：所有翻译结果均经过严格的质量控制，确保准确性和流畅性。
4. SFT 友好：数据结构完全符合指令微调的标准格式，可直接用于训练。

## 主要参与者
- [歸藏 (guizang.ai)](https://x.com/op7418)
- [FradSer](https://x.com/FradSer)

## 许可证
本数据集基于 [Creative Commons NonCommercial (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/legalcode) 许可发布。 