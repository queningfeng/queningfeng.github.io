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

I have published **11** peer-reviewed papers and preprints, including an **early-accepted MICCAI 2025** paper as co-first author. My total <a href='https://scholar.google.com/citations?user=ZxrkoP4AAAAJ'>Google Scholar citations <strong><span id='total_cit'>—</span></strong></a> are updated automatically every day. You can also use the Google Scholar badge <a href='https://scholar.google.com/citations?user=ZxrkoP4AAAAJ'><img src="https://img.shields.io/endpoint?url={{ url | url_encode }}&logo=Google%20Scholar&labelColor=f6f6f6&color=9cf&style=flat&label=citations" alt="Google Scholar citations"></a>.

I am always happy to discuss research and open to collaboration — feel free to reach out by email.

# 🔥 News
- *2026.10*: &nbsp;🎉 **OncoRelay3D**, a foundation-model-assisted framework that reconstructs 3D tumour cell-expression fields for mechanism-aware directed cell–cell communication, is accepted to the **MICCAI 2026 CMMCA Workshop**.
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

<sup>†</sup> **Equal contribution (co-first author).** &nbsp; <sup>✉</sup> **Corresponding author.** &nbsp; My name is shown in **bold**.

{% include publications.html %}

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
