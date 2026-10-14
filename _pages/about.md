---
permalink: /
title: ""
excerpt: ""
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---

{% if site.google_scholar_stats_use_cdn %}
{% assign gsDataBaseUrl = "https://cdn.jsdelivr.net/gh/" | append: site.repository | append: "@" %}
{% else %}
{% assign gsDataBaseUrl = "https://raw.githubusercontent.com/" | append: site.repository | append: "/" %}
{% endif %}
{% assign url = gsDataBaseUrl | append: "google-scholar-stats/gs_data_shieldsio.json" %}

<span class='anchor' id='about-me'></span>

# 👋 About Me

I am a Ph.D. student at the **State Key Laboratory of Natural and Biomimetic Drugs, Department of Biomedical Engineering, College of Future Technology, Peking University**, Beijing, China. Before joining PKU, I studied at the College of Medicine and Biological Information Engineering, **Northeastern University (China)**, Shenyang.

<!-- TODO 可选：把你的导师名字加进来，例如
     advised by Prof. XXX, and previously worked with Prof. Yin Dai and Prof. Yueyang Teng at Northeastern University. -->

My research sits at the intersection of **spatial transcriptomics**, **computational pathology** and **medical image analysis**. I build multimodal and generative models that recover the molecular and spatial information current spatial omics platforms cannot measure directly, and I care about making these models reliable enough for downstream biological discovery. Concretely, I work on:

- **Spatial transcriptomics interpolation and enhancement** — reconstructing missing tissue sections, and coordinating molecular / spatial fidelity across platforms.
- **Histology-aware spatial modelling** — using paired H&E images as an explicit anatomical constraint for cell–cell communication inference.
- **Cross-modal medical image analysis** — joint interpolation and segmentation, low-dose CT denoising, and medical image fusion.

I have published **10** peer-reviewed papers and preprints, including an **early-accepted MICCAI 2025** paper as first author. My total <a href='https://scholar.google.com/citations?user=ZxrkoP4AAAAJ'>Google Scholar citations <strong><span id='total_cit'>—</span></strong></a> are updated automatically every day. You can also use the Google Scholar badge <a href='https://scholar.google.com/citations?user=ZxrkoP4AAAAJ'><img src="https://img.shields.io/endpoint?url={{ url | url_encode }}&logo=Google%20Scholar&labelColor=f6f6f6&color=9cf&style=flat&label=citations" alt="Google Scholar citations"></a>.

I am always happy to discuss research and open to collaboration — feel free to reach out by email.

# 🔥 News
- *2026.10*: &nbsp;🎉 Our spatial transcriptomics enhancement foundation model **FOCUS** is updated on bioRxiv (v3) and retitled *Coordinated Enhancement of Molecular and Spatial Fidelity for Biological Inference in Spatial Transcriptomics*.
- *2026.10*: &nbsp;📄 **HARMONIC**, our histology-aware graph framework for cell–cell communication inference, is updated on bioRxiv (v3).
- *2026.08*: &nbsp;🎉 **CoInS-Net**, a continuous position-aware network for joint medical image interpolation and segmentation, is released on arXiv. *(co-first author)*
- *2026.05*: &nbsp;🎉 **StateXDiff**, a cell state-contextualized multimodal diffusion model for single-cell perturbation prediction, is released on arXiv. *(co-first author)*
- *2025.12*: &nbsp;📄 Our multimodal generative foundation model for cross-platform spatial transcriptomics enhancement is released on bioRxiv. *(co-first author)*
- *2025.12*: &nbsp;📄 Our review on hydrogel-based electronic skins is published in *Advanced Functional Materials*.
- *2025.06*: &nbsp;🎉 **C2-STi** is **early accepted** to **MICCAI 2025** — the first attempt at interpolating missing spatial transcriptomics slices at arbitrary intermediate positions.
- *2025.05*: &nbsp;📄 **C2-STi** preprint is available on arXiv ([2505.10729](https://arxiv.org/abs/2505.10729)).
- *2025.02*: &nbsp;📄 **MLAR-UNet** is published in *Physics in Medicine & Biology*. *(co-first author)*

# 📝 Publications

<sup>†</sup> **Equal contribution / co-first author.** &nbsp; My name is shown in **bold**.

## First-author & Co-first-author Work

- <span class="pub-venue">bioRxiv 2026</span> [**Coordinated Enhancement of Molecular and Spatial Fidelity for Biological Inference in Spatial Transcriptomics**](https://doi.org/10.64898/2025.12.23.696267)  
  Xiao-Fei Wang, **Ningfeng Que**<sup>†</sup>, Hanyu Liu, Chen-Yang Tao, Yu Jiang, Yi-Xuan Jiang, Pinan Zhu, Jian-Guo Xu, Han Yan, Bing Ye, Stephen J. Price, Jianzhong Jeff Xi, Xinjie Wang, Chao Li  
  <span class="pub-note">FOCUS — a multimodal generative foundation model for coordinated spatial transcriptomics enhancement.</span> <span class="show_paper_citations" data-title="Coordinated Enhancement of Molecular and Spatial Fidelity for Biological Inference in Spatial Transcriptomics"></span>

- <span class="pub-venue">arXiv 2026</span> [**CoInS-Net: A Continuous Position-Aware Network for Joint Medical Image Interpolation and Segmentation**](https://arxiv.org/abs/2608.09391)  
  Yujia Sun, **Ningfeng Que**<sup>†</sup>, Peiting Shi, Rongrong Fu, Yingying Yang, Xinhang Li, Yin Dai  
  <span class="pub-note">Bidirectional task interaction under a shared Swin encoder with continuous spatial coordinate queries.</span> <span class="show_paper_citations" data-title="CoInS-Net: A Continuous Position-Aware Network for Joint Medical Image Interpolation and Segmentation"></span>

- <span class="pub-venue">arXiv 2026</span> [**StateXDiff: Cell State-Contextualized Multimodal Diffusion for Single-Cell Perturbation Prediction**](https://arxiv.org/abs/2605.16104)  
  Peiting Shi, **Ningfeng Que**<sup>†</sup>, Xianzhe Huang, Xiaofei Wang, Jianzhong Jeff Xi  
  <span class="pub-note">Cell-state-conditioned multimodal diffusion for predicting single-cell perturbation responses.</span> <span class="show_paper_citations" data-title="StateXDiff: Cell State-Contextualized Multimodal Diffusion for Single-Cell Perturbation Prediction"></span>

- <span class="pub-venue">MICCAI 2025</span> [**Adaptive Spatial Transcriptomics Interpolation via Cross-modal Cross-slice Modeling**](https://arxiv.org/abs/2505.10729)  
  **Ningfeng Que**, Xiaofei Wang, Jingjing Chen, Yixuan Jiang, Chao Li  
  <span class="pub-note">C2-STi — **Early Accept**. The first method to interpolate missing ST slices at arbitrary intermediate positions, fusing paired H&E images through cross-modal alignment.</span> <span class="show_paper_citations" data-title="Adaptive Spatial Transcriptomics Interpolation via Cross-modal Cross-slice Modeling"></span> [\[code\]](https://github.com/XiaofeiWang2018/C2-STi)

- <span class="pub-venue">PMB 2025</span> [**MLAR-UNet: LDCT image denoising based on U-Net with multiple lightweight attention-based modules and residual reinforcement**](https://doi.org/10.1088/1361-6560/adb19a)  
  Hao Tang, **Ningfeng Que**<sup>†</sup>, Yanwen Tian, Mingzhe Li, Alessandro Perelli, Yueyang Teng  
  <span class="pub-note">Lightweight attention modules plus residual reinforcement for low-dose CT denoising.</span> <span class="show_paper_citations" data-title="MLAR-UNet: LDCT image denoising based on U-Net with multiple lightweight attention-based modules and residual reinforcement"></span>

- <span class="pub-venue">IJIST 2024</span> [**VTCNet: A Feature Fusion DL Model Based on CNN and ViT for the Classification of Cervical Cells**](https://doi.org/10.1002/ima.23161)  
  Mingzhe Li, **Ningfeng Que**<sup>†</sup>, Juanhua Zhang, Pingfang Du, Yin Dai  
  <span class="pub-note">CNN–ViT feature fusion for cervical cell classification.</span> <span class="show_paper_citations" data-title="VTCNet: A Feature Fusion DL Model Based on CNN and ViT for the Classification of Cervical Cells"></span>

## Collaborative Work

- <span class="pub-venue">bioRxiv 2026</span> [**Histology-aware Inference of Cell-cell Communication in Spatial Transcriptomics**](https://doi.org/10.64898/2026.01.22.701166)  
  Xiaofei Wang, Chenyang Tao, Yu Jiang, Yixuan Jiang, Hanyu Liu, Zheng Jiang, Pinan Zhu, **Ningfeng Que**, Jianzhong Xi, Stephen Price, Bin Qian, Jian-Guo Xu, Chao Li  
  <span class="pub-note">HARMONIC — a histology-aware graph learning framework for anatomically contextualized cell–cell communication inference.</span> <span class="show_paper_citations" data-title="Histology-aware Inference of Cell-cell Communication in Spatial Transcriptomics"></span>

- <span class="pub-venue">AFM 2025</span> [**Advances in Hydrogel-Based Electronic Skins: From Material Design to Multifunctional Applications**](https://doi.org/10.1002/adfm.202527525)  
  Deliang Li, **Ningfeng Que**, Hao Tang, Yanwen Tian, Chenxi Jing, Le Liu, Guanshi Liu, Hongxing Zhou, Wenwen Zhang, Hongguo Wei, Ye Tian  
  <span class="pub-note">Review on hydrogel-based electronic skins, from material design to multifunctional applications.</span> <span class="show_paper_citations" data-title="Advances in Hydrogel-Based Electronic Skins: From Material Design to Multifunctional Applications"></span>

- <span class="pub-venue">IJCAI 2024</span> [**Multi-scale Context-Aware Networks Based on Fragment Association for Human Activity Recognition**](https://doi.org/10.24963/ijcai.2024/351)  
  Zhiqiong Wang, Hanyu Liu, Boyang Zhao, Qi Shen, Mingzhe Li, **Ningfeng Que**, Mingke Yan, Junchang Xin  
  <span class="pub-note">Multi-scale context-aware modelling with fragment association for human activity recognition.</span> <span class="show_paper_citations" data-title="Multi-scale Context-Aware Networks Based on Fragment Association for Human Activity Recognition"></span>

- <span class="pub-venue">CBM 2024</span> [**DesTrans: A medical image fusion method based on Transformer and improved DenseNet**](https://doi.org/10.1016/j.compbiomed.2024.108463)  
  Yumeng Song, Yin Dai, Weibin Liu, Yue Liu, Xinpeng Liu, Qiming Yu, Xinghan Liu, **Ningfeng Que**, Mingzhe Li  
  <span class="pub-note">Transformer plus improved DenseNet for medical image fusion.</span> <span class="show_paper_citations" data-title="DesTrans: A medical image fusion method based on Transformer and improved DenseNet"></span>

# 📖 Educations

<!-- TODO 确认年份：下面两段的起止时间是我根据论文署名时间推断的，请核对后再上线。 -->

- *2025.09 - now*, Ph.D. in Biomedical Engineering, State Key Laboratory of Natural and Biomimetic Drugs, Department of Biomedical Engineering, College of Future Technology, **Peking University**, Beijing, China.
- *2022.09 - 2025.06*, M.S. in Biomedical Engineering, College of Medicine and Biological Information Engineering, **Northeastern University**, Shenyang, China.

<!--
=====================================================================
下面三节等你的内容到了再打开。现在整段是 HTML 注释，不会渲染，
顶部导航里对应条目也已经注释掉了。
另外记得把 _data/navigation.yml 里对应三行一起取消注释。

# 🎖 Honors and Awards
- *2025* 你的获奖

# 💻 Internships
- *2024.06 - 2024.09*, 单位, 城市。

# 📚 Academic Services
- 会议审稿人 / 期刊审稿人

=====================================================================
-->
