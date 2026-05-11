# 深度学习

## 一、神经网络基础

### 1.1 人工神经网络

人工神经网络（Artificial Neural Network, ANN）是受生物神经系统启发的计算模型。1943年，沃伦·麦卡洛克（Warren McCulloch）和沃尔特·皮茨（Walter Pitts）提出了第一个神经元数学模型。1958年，弗兰克·罗森布拉特（Frank Rosenblatt）发明了感知机（Perceptron），这是第一个可以学习的神经网络模型。

多层感知机（MLP）通过引入隐藏层和非线性激活函数解决了感知机无法处理非线性问题（如XOR问题）的缺陷。反向传播算法由保罗·韦博斯（Paul Werbos）于1974年提出，大卫·鲁梅尔哈特（David Rumelhart）等人于1986年将其推广，使得多层神经网络的训练成为可能。

### 1.2 激活函数

激活函数引入非线性，是神经网络表达能力的核心。常用的激活函数包括：

- **Sigmoid**：将输入映射到(0,1)区间，但存在梯度消失问题
- **Tanh**：将输入映射到(-1,1)区间，零中心化但仍有梯度消失
- **ReLU**（Rectified Linear Unit）：由哈恩（Hahnloser）等人于2000年提出，计算高效，缓解了梯度消失问题，是目前最常用的激活函数
- **Leaky ReLU**：解决ReLU的"神经元死亡"问题
- **GELU**（Gaussian Error Linear Unit）：被GPT和BERT系列模型采用
- **Swish**：由Google Brain团队提出，在部分任务上优于ReLU

### 1.3 损失函数与优化器

损失函数衡量模型预测与真实值之间的差异。均方误差（MSE）用于回归任务，交叉熵损失（Cross-Entropy Loss）用于分类任务。

优化器决定了模型参数的更新策略。随机梯度下降（SGD）是最基础的优化器。Adam优化器由迪德里克·金马（Diederik Kingma）和吉米·巴（Jimmy Ba）于2015年提出，结合了动量和自适应学习率的优点，是目前最流行的深度学习优化器。AdamW由洛里奇（Loshchilov）和胡特（Hutter）提出，修正了Adam中权重衰减的实现方式，在训练大语言模型时广泛使用。

## 二、卷积神经网络

### 2.1 CNN的发展历程

卷积神经网络（Convolutional Neural Network, CNN）是一类专门处理网格状数据（如图像）的深度学习模型。CNN的核心组件包括卷积层、池化层和全连接层。

1989年，杨立昆（Yann LeCun）开发了LeNet-5，用于手写数字识别，这是CNN的首次成功应用。2012年，亚历克斯·克里泽夫斯基（Alex Krizhevsky）等人提出AlexNet，在ImageNet竞赛中将错误率降低了约10个百分点，引爆了深度学习革命。

2014年，牛津大学视觉几何组提出VGGNet，证明了使用小卷积核（3×3）构建深层网络的有效性。同年，Google团队提出GoogLeNet（Inception Net），引入了Inception模块。微软亚洲研究院的何恺明等人提出ResNet（残差网络），通过残差连接解决了深层网络的退化问题，使得训练数百层的网络成为可能。ResNet是深度学习史上最具影响力的架构之一。

### 2.2 特征提取

CNN通过逐层卷积提取从低级到高级的特征。浅层卷积核学习边缘、纹理等低级特征；深层卷积核学习物体部件、整体形状等高级特征。转移学习（Transfer Learning）利用预训练模型在大规模数据集上学到的特征，可以显著减少目标任务所需的训练数据和计算资源。

### 2.3 目标检测

目标检测（Object Detection）任务需要同时定位和识别图像中的物体。R-CNN由罗斯·吉里克（Ross Girshick）等人提出，开创了基于区域提名的检测框架。Faster R-CNN引入了区域建议网络（RPN），实现了端到端的目标检测。

YOLO（You Only Look Once）由约瑟夫·雷德蒙（Joseph Redmon）等人提出，将目标检测视为回归问题，实现了实时检测。YOLO系列不断发展，YOLOv5、YOLOv7、YOLOv8等版本在速度和精度上持续改进。

SSD（Single Shot MultiBox Detector）由刘威（Wei Liu）等人提出，在不同尺度的特征图上进行检测，兼顾速度和精度。中国科学院自动化研究所在小目标检测方面做了大量研究。

### 2.4 图像分割

语义分割（Semantic Segmentation）将图像中的每个像素分配到特定类别。全卷积网络（FCN）由龙凯利（Jonathan Long）等人于2015年提出，将分类网络转化为分割网络。U-Net由奥尔拉夫·龙内贝格尔（Olaf Ronneberger）于2015年提出，最初用于生物医学图像分割，其编码器-解码器结构成为图像分割的标准范式。

实例分割（Instance Segmentation）需要区分同一类别的不同实例。Mask R-CNN在Faster R-CNN的基础上增加了一个分割分支。何恺明的团队提出的PointRend通过迭代细化分割边界来提升分割质量。

## 三、循环神经网络

### 3.1 RNN基础结构

循环神经网络（Recurrent Neural Network, RNN）是处理序列数据的神经网络架构。RNN通过隐藏状态在时间步之间传递信息，理论上可以捕获任意长度的序列依赖。但在实践中，标准RNN存在梯度消失和梯度爆炸问题，难以学习长程依赖。

### 3.2 LSTM与GRU

长短期记忆网络（Long Short-Term Memory, LSTM）由塞普·霍赫赖特（Sepp Hochreiter）和于尔根·施密德胡伯（Jürgen Schmidhuber）于1997年提出。LSTM通过引入门控机制（输入门、遗忘门、输出门）和细胞状态，有效解决了梯度消失问题，能够学习长程依赖关系。

门控循环单元（Gated Recurrent Unit, GRU）由曹凯（Kyunghyun Cho）等人于2014年提出，将LSTM的三个门简化为两个门（重置门和更新门），参数更少，训练更快。

### 3.3 序列到序列模型

序列到序列（Seq2Seq）模型由伊利亚·苏茨克韦尔（Ilya Sutskever）等人于2014年提出，由编码器和解码器两个RNN组成，广泛应用于机器翻译、文本摘要等任务。注意力机制（Attention Mechanism）由巴德诺（Bahdanau）等人于2015年提出，允许解码器在每一步动态关注输入序列的不同位置，显著提升了Seq2Seq模型的性能。

## 四、Transformer架构

### 4.1 自注意力机制

Transformer由艾什维什·瓦斯瓦尼（Ashish Vaswani）等Google Brain团队成员于2017年在论文《Attention Is All You Need》中提出。Transformer完全基于自注意力（Self-Attention）机制，摒弃了RNN的递归结构，可以并行处理序列中的所有位置。

自注意力机制通过查询（Query）、键（Key）、值（Value）三个矩阵计算注意力权重。缩放点积注意力（Scaled Dot-Product Attention）的公式为：Attention(Q,K,V) = softmax(QK^T / √d_k)V。

多头注意力（Multi-Head Attention）允许模型同时关注不同子空间的信息，增强了模型的表达能力。位置编码（Positional Encoding）弥补了Transformer缺乏位置感知的问题，常用的有正弦位置编码和旋转位置编码（RoPE）。

### 4.2 Transformer的变体

Vision Transformer（ViT）由谷歌团队于2020年提出，将图像分割为固定大小的图块（Patch），将其作为序列输入Transformer，在图像分类任务上超越了CNN。Swin Transformer由微软亚洲研究院的刘泽等人提出，引入了移动窗口（Shifted Window）机制，降低了计算复杂度。

北京大学、清华大学和阿里巴巴达摩院联合提出了许多Transformer优化方案。中国科学院计算技术研究所在Transformer的硬件加速方面做了重要工作。

## 五、生成对抗网络

### 5.1 GAN基本原理

生成对抗网络（Generative Adversarial Network, GAN）由伊恩·古德费洛（Ian Goodfellow）于2014年提出。GAN由生成器（Generator）和判别器（Discriminator）组成，两者通过对抗训练相互提升。生成器尝试生成逼真的假数据，判别器尝试区分真假数据。

### 5.2 GAN的重要变体

DCGAN将卷积神经网络引入GAN架构。条件GAN（CGAN）通过引入条件信息实现可控生成。StyleGAN由英伟达（NVIDIA）的提罗·卡拉斯（Tero Karras）等人提出，通过风格控制实现高分辨率图像生成。CycleGAN由朱俊彦（Jun-Yan Zhu）等人提出，实现了无配对数据的图像到图像转换。

### 5.3 中国在GAN领域的研究

中国科学院自动化研究所的生成式模型研究团队在图像生成方面做了大量工作。商汤科技（SenseTime）在GAN的商业应用方面处于领先地位，特别是在人脸生成和视频合成领域。旷视科技（Megvii）利用GAN进行数据增强，提升了人脸识别系统的鲁棒性。

## 六、深度学习框架与工具

### 6.1 主流深度学习框架

TensorFlow由Google Brain团队于2015年开源，提供了完整的深度学习生态系统。PyTorch由Facebook AI Research（现Meta AI）于2016年发布，以动态计算图和Pythonic接口著称，在研究领域占据主导地位。百度飞桨（PaddlePaddle）是中国首个开源开放的产业级深度学习框架，提供了丰富的预训练模型库和端到端开发套件。

华为昇思（MindSpore）是华为推出的全场景深度学习框架，支持端、边、云全场景协同。清华大学和旷视科技联合开发的天元（MegEngine）深度学习框架注重推理效率。

### 6.2 GPU与专用加速芯片

NVIDIA的GPU是深度学习训练的主力硬件。CUDA并行计算平台由NVIDIA于2007年推出，使得GPU可以被用于通用计算。NVIDIA A100和H100 GPU是目前深度学习训练的主流选择。

华为昇腾（Ascend）系列AI芯片是国产AI加速器的代表。昇腾910用于训练场景，昇腾310用于推理场景。寒武纪（Cambricon）推出的思元系列AI芯片在推理场景中有广泛应用。地平线（Horizon Robotics）的征程系列芯片专注于智能驾驶场景。
