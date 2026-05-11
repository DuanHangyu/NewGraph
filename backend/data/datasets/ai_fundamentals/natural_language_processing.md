# 自然语言处理

## 一、自然语言处理概述

自然语言处理（Natural Language Processing, NLP）是人工智能和语言学的交叉学科，目标是让计算机能够理解、解释和生成人类语言。NLP的发展经历了从基于规则的方法到统计方法再到深度学习方法的演进。

中国科学院计算技术研究所是国内最早开展NLP研究的机构之一。清华大学计算机科学与技术系的自然语言处理实验室（THUNLP）在国际上享有盛誉。北京大学计算语言学教育部重点实验室在中文信息处理方面处于领先地位。哈尔滨工业大学社会计算与信息检索研究中心（SCIR）在机器翻译和文本生成方面有深厚积累。

## 二、文本预处理

### 2.1 中文分词

中文分词是中文NLP的基础任务，因为中文文本不像英文那样天然有空格分隔词语。常用的分词方法包括基于词典的最大匹配法、基于隐马尔可夫模型（HMM）的方法和基于条件随机场（CRF）的方法。

jieba分词是最流行的Python中文分词工具，采用基于前缀词典的分词算法。清华大学开发的THULAC（THU Lexical Analyzer for Chinese）在准确率上有优势。哈工大语言技术平台（LTP）提供了一套完整的中文语言处理工具链。

### 2.2 词向量

词向量（Word Embedding）将词语映射到低维稠密向量空间，使语义相近的词在向量空间中距离相近。Word2Vec由托马斯·米科洛夫（Tomas Mikolov）等Google团队于2013年提出，包含CBOW和Skip-gram两种模型。GloVe（Global Vectors）由斯坦福大学开发，结合了全局统计信息和局部上下文窗口。

ELMo（Embeddings from Language Models）由艾伦AI研究所（Allen AI）的马修·彼得斯（Matthew Peters）等人于2018年提出，通过双向LSTM语言模型生成上下文相关的词表示，解决了多义词问题。

## 三、预训练语言模型

### 3.1 BERT

BERT（Bidirectional Encoder Representations from Transformers）由Google的雅各布·德夫林（Jacob Devlin）等人于2018年提出。BERT的核心创新是通过掩码语言模型（MLM）和下一句预测（NSP）两个预训练任务，实现了真正的双向上下文表示学习。

BERT在11项NLP基准任务上刷新了记录。BERT-base包含1.1亿参数，BERT-large包含3.4亿参数。BERT的出现开启了预训练-微调（Pre-train and Fine-tune）的NLP新范式。

哈工大讯飞联合实验室（HFL）发布了中文BERT系列模型。百度基于知识增强的持续学习语义理解框架ERNIE（Enhanced Representation through Knowledge Integration）在中文NLP任务上表现优异。ERNIE通过引入知识图谱中的实体信息和短语级别的掩码，提升了中文语义理解能力。

### 3.2 GPT系列

GPT（Generative Pre-trained Transformer）由OpenAI开发。GPT-1于2018年发布，使用Transformer解码器进行单向语言模型预训练。GPT-2于2019年发布，参数量达到15亿，展示了无监督预训练的强大能力。

GPT-3于2020年发布，参数量达到1750亿，展示了强大的上下文学习（In-Context Learning）能力。InstructGPT和ChatGPT通过人类反馈的强化学习（RLHF）技术对齐模型行为与人类偏好。

### 3.3 中国的大语言模型

百度文心一言（ERNIE Bot）基于文心大模型，在中文理解和生成方面表现突出。阿里巴巴通义千问（Qwen）系列模型在多个国际评测中表现优异，Qwen-72B在多项基准测试中达到同量级最优。智谱AI的GLM（General Language Model）系列采用自回归填空预训练策略，ChatGLM系列开源模型在国内开发者中广泛使用。

月之暗面（Moonshot AI）的Kimi智能助手以长文本处理能力著称。MiniMax的abab系列模型在多模态生成方面有优势。百川智能的Baichuan系列开源模型为中文NLP社区提供了重要资源。零一万物（01.AI）的Yi系列模型在开源社区获得了广泛关注。深度求索（DeepSeek）推出的DeepSeek系列模型，特别是DeepSeek-V3和DeepSeek-R1，在推理能力上达到国际领先水平。

## 四、机器翻译

### 4.1 统计机器翻译

统计机器翻译（SMT）基于统计模型从平行语料中学习翻译规则。IBM模型系列是早期的经典方法。基于短语的翻译系统（Phrase-based SMT）在2000年代是主流方法。Moses是开源SMT系统的代表。

### 4.2 神经机器翻译

神经机器翻译（NMT）使用端到端的神经网络进行翻译。Google在2016年从SMT切换到NMT系统。百度在2015年较早地将NMT应用于在线翻译系统。字节跳动的火山翻译在低资源语言翻译方面有重要突破。

### 4.3 同声传译

同声传译（Simultaneous Interpretation）是机器翻译中最具挑战性的任务之一，需要在源语言句子未完成时就开始翻译。百度研究院在语音到语音的同传系统方面有重要进展。科大讯飞（iFLYTEK）的讯飞听见产品在会议同传场景中广泛应用。

## 五、文本分类与情感分析

### 5.1 文本分类

文本分类将文本自动归类到预定义的类别中。典型应用包括新闻分类、垃圾邮件过滤、意图识别等。从传统方法（朴素贝叶斯、SVM）到深度学习方法（TextCNN、BiLSTM、BERT微调），文本分类的准确率持续提升。

### 5.2 情感分析

情感分析（Sentiment Analysis）识别文本中表达的情感倾向。细粒度情感分析可以识别文本中的方面级（Aspect-level）情感。美团、阿里巴巴等公司在用户评论分析中大规模应用情感分析技术。

## 六、信息抽取

### 6.1 命名实体识别

命名实体识别（Named Entity Recognition, NER）从文本中识别出人名、地名、组织名等命名实体。中文NER由于缺乏词边界信息，比英文更具挑战性。百度UIR团队和中国科学院在中文NER方面有深入研究。

### 6.2 关系抽取

关系抽取（Relation Extraction）识别实体之间的语义关系。远程监督（Distant Supervision）通过知识图谱自动标注训练数据。清华大学在关系抽取方面有系统性的研究。

### 6.3 事件抽取

事件抽取（Event Extraction）从文本中识别事件及其论元。中国科学院软件研究所在事件抽取方面有重要贡献。事件抽取在金融风控、舆情监测等领域有广泛应用。

## 七、问答系统

### 7.1 检索式问答

检索式问答（Retrieval-based QA）从知识库中检索相关文档或段落来回答问题。百度知道和知乎的问答推荐系统使用检索式方法。中国科学院计算技术研究所在大规模知识检索方面做了重要工作。

### 7.2 知识图谱问答

知识图谱问答（KGQA）将自然语言问题转化为对知识图谱的查询。问题理解、实体链接和语义解析是KGQA的核心步骤。北京大学王选计算机研究所在知识图谱问答方面有深入研究。

### 7.3 生成式问答

生成式问答（Generative QA）使用大语言模型直接生成答案。检索增强生成（RAG，Retrieval-Augmented Generation）由Meta AI于2020年提出，结合了检索和生成的优势。RAG通过外部知识库约束LLM的生成，减少幻觉并增强可信度。

## 八、语音识别与合成

### 8.1 语音识别

自动语音识别（Automatic Speech Recognition, ASR）将语音信号转换为文本。隐马尔可夫模型（HMM）曾是主流方法，深度学习时代的主流方法包括CTC（Connectionist Temporal Classification）和注意力机制的端到端模型。科大讯飞在中文语音识别领域处于全球领先地位，Whisper模型由OpenAI开发，在多语言语音识别上表现优异。

### 8.2 语音合成

语音合成（Text-to-Speech, TTS）将文本转换为语音。Tacotron和WaveNet是深度学习TTS的里程碑。百度Deep Voice系列实现了实时神经语音合成。微软亚洲研究院在多语言语音合成方面有重要贡献。字节跳动在语音合成和声音克隆方面技术领先。
