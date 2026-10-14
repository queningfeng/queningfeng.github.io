# Ningfeng Que — 个人学术主页

基于 [AcadHomepage](https://github.com/RayeRen/acad-homepage.github.io)（MIT 许可）定制的个人学术主页，
部署在 GitHub Pages 上，**引用数由 GitHub Actions 每天自动更新**。

线上地址（部署后）：<https://queningfeng.github.io>

---

## 一、上线前必须改的 3 处

这三处是占位符，不改会直接显示在公开页面上：

| # | 文件 | 改什么 |
|---|------|--------|
| 1 | `_config.yml` | `author.email` 里的 `YOUR_EMAIL@stu.pku.edu.cn` → 你的真实邮箱 |
| 2 | `_pages/about.md` | `# 📖 Educations` 那两段的**起止年份**（我按论文署名时间推断的，请核对） |
| 3 | `images/avatar.jpg` | 换成本人照片（现在是「NQ」首字母占位图） |

### 建议改的

- `_config.yml` 里 `author.bio` / `location` / `employer` 的措辞。
- `_pages/about.md` 里 `# 👋 About Me` 末段"open to collaboration"那句，可以写得更具体。
- 有获奖 / 实习 / 审稿经历的话，`_pages/about.md` 文件末尾有一整段被 `<!-- -->` 注释掉的模板，
  取消注释填上内容即可；同时把 `_data/navigation.yml` 里对应三行的 `# ` 去掉。

---

## 二、目录结构

```
├── _config.yml                  # 站点与作者信息（改动最频繁的地方）
├── _data/navigation.yml         # 顶部导航栏
├── _pages/about.md              # 主页全部内容：简介 / News / 论文 / 教育经历
├── _includes/
│   ├── author-profile.html      # 侧边栏（由 _config.yml 的 author 段驱动）
│   ├── fetch_google_scholar_stats.html   # 读取引用数据并回填页面的 JS
│   └── head/custom.html         # favicon / SEO meta
├── assets/css/main.scss         # 样式，论文徽章等自定义样式在文件末尾
├── images/                      # 头像与 favicon
├── google_scholar_crawler/      # 抓取引用数的 Python 脚本 + 测试
│   ├── main.py
│   ├── test_crawler.py          # 跑：python test_crawler.py
│   └── requirements.txt
├── tools/generate_images.py     # 重新生成头像 / favicon
└── .github/workflows/google_scholar_crawler.yaml   # 每天自动更新引用数
```

---

## 三、本地预览

GitHub Pages 用 Jekyll 在服务器端构建，所以**不装 Ruby 也能部署**。
想本地预览则需要 Ruby：

```bash
# 1. 安装 Ruby（Windows 上装 RubyInstaller，勾选 DevKit）
# 2. 安装依赖
bundle install
# 3. 启动（改代码会自动刷新）
bash run_server.sh
# 4. 打开 http://127.0.0.1:4000
```

> `bash run_server.sh` 里其实就是 `bundle exec jekyll serve --livereload`，
> 在 PowerShell 里直接跑这一条也行。

---

## 四、部署到 GitHub Pages

### 1. 创建仓库

必须是**公开**仓库，且仓库名**必须**是 `queningfeng.github.io`，这样地址才会是
`https://queningfeng.github.io`。

### 2. 推送代码

```bash
cd queningfeng.github.io
git add -A
git commit -m "init: personal academic homepage"
git branch -M main
git remote add origin https://github.com/queningfeng/queningfeng.github.io.git
git push -u origin main
```

### 3. 打开 Pages 并放行 Actions

1. 仓库 **Settings → Pages**：Source 选 `Deploy from a branch`，Branch 选 `main` / `(root)`，保存。
2. 仓库 **Actions** 标签页，如果顶部有提示，点 *"I understand my workflows, go ahead and enable them"*。

### 4. 首次生成引用数据

进入 **Actions → Update Google Scholar citations → Run workflow** 手动跑一次。
跑完后仓库里会多出一个 `google-scholar-stats` 分支，主页上的引用数就会显示出来。

**不需要配置任何 Secret**：Scholar ID 和 ORCID 都写在 `main.py` 里作为默认值（它们本来就是公开信息）。
想覆盖的话，在 **Settings → Secrets and variables → Actions** 里加同名的 `GOOGLE_SCHOLAR_ID` / `ORCID` 即可。

---

## 五、引用数是怎么自动更新的

```
GitHub Actions（每天 UTC 08:00）
   └─ 跑 google_scholar_crawler/main.py
        ├─ 优先用 scholarly 爬 Google Scholar  ← 最权威
        └─ 被抓/被限流时退回 OpenAlex（按 ORCID 查）  ← 兜底
   └─ 结果写成 results/gs_data.json
   └─ 推到 google-scholar-stats 分支（覆盖式，不污染 main）
        ↓
主页 JS（fetch_google_scholar_stats.html）读这个 JSON，回填页面上的引用数
```

**为什么不用官方模板的做法？** 官方模板用「Google Scholar 论文簇 ID」当键去查引用数，
而那个 ID 只有爬虫成功跑过一次之后才有（而且每次新增论文都要手动补）。
这里改成**按论文标题匹配**（两端做同样的归一化），所以你只要在 `about.md` 里写
`data-title="论文标题"`，引用数就会自动对上，不需要任何内部 ID。

对应的论文条目长这样：

```html
<span class="show_paper_citations"
      data-title="Adaptive Spatial Transcriptomics Interpolation via Cross-modal Cross-slice Modeling"></span>
```

> 标题只要"归一化后一致"就行——大小写、空格、标点、`&amp;` 之类的差异都会被忽略。
> 两端算法必须一致，`google_scholar_crawler/test_crawler.py` 会直接从
> `_includes/fetch_google_scholar_stats.html` 里把 JS 函数抽出来跟 Python 对拍，防止以后改歪。

---

## 六、共同一作（co-first author）怎么标

论文条目在作者列表里给你的名字加 `<sup>†</sup>`，页面顶部已有图例说明
`†` 表示 **Equal contribution / co-first author**：

```markdown
- <span class="pub-venue">arXiv 2026</span> [**CoInS-Net: ...**](https://arxiv.org/abs/2608.09391)
  Yujia Sun, **Ningfeng Que**<sup>†</sup>, Peiting Shi, ...
```

目前标记为共同一作的 5 篇：`FOCUS (bioRxiv 2026)`、`CoInS-Net`、`StateXDiff`、`MLAR-UNet`、`VTCNet`。
其余按真实署名位置展示，不做任何美化——**共同一作与第二作者在页面上是区分开的**。

---

## 七、常见问题

**主页引用数一直显示 "—"**
1. 确认 Actions 至少成功跑过一次，且仓库里存在 `google-scholar-stats` 分支。
2. `_config.yml` 里的 `repository` 必须**恰好**是你的 `用户名/仓库名`，否则数据地址拼错。
3. 用的是 jsDelivr CDN，分支刚更新时可能有缓存；把 `google_scholar_stats_use_cdn` 改成 `false`
   可以立刻排查是不是缓存问题（JS 里已经加了按小时变化的 cache buster 来缓解）。

**Actions 里 Google Scholar 那步失败**
这是常态，Google 会封 Actions 的机房 IP。脚本会自动退回 OpenAlex，页面照常更新，
只是数字会比 Google Scholar 略少一点（OpenAlex 收录有延迟）。日志里会写明
`source=openalex`，页面上对应的 tooltip 也会标注数据来源。

**想立刻手动更新一次**
Actions 页面 → Update Google Scholar citations → Run workflow。

**改了论文列表但引用数没变**
`about.md` 里的 `data-title` 必须和 Google Scholar 上的标题能对上（归一化后一致）。
新增论文后可以先本地跑 `python google_scholar_crawler/test_crawler.py` 检查标题数量。

**头像 / favicon 想换成自己的照片**
把照片存成 `images/avatar.jpg` 后运行：

```bash
python tools/generate_images.py --from-avatar
```

会自动从照片裁出方形并生成整套 favicon。

---

## 八、许可与致谢

- 模板：[AcadHomepage](https://github.com/RayeRen/acad-homepage.github.io)（MIT），
  它本身基于 [Minimal Mistakes](https://github.com/mmistakes/minimal-mistakes)；
  字体图标来自 Font Awesome（SIL OFL 1.1 / MIT）与 Academicons。
- 本仓库的定制部分（论文数据整理、按标题匹配的引用回填、爬虫兜底逻辑、测试）同样以 MIT 发布，
  详见 `LICENSE`。
