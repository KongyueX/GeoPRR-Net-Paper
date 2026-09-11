# GeoPRR-Net / Electronics Overleaf 上传包

当前数据使用 SyncG 官方 16,000 张训练图和 4,000 张测试图。论文按 SyncG → zero-shot → 读出头适配比较 → 核心变体比较 → 效率的顺序组织；主比较统一采用自动 ROI 读数路径、NMAE、Acc@5% 和 Coverage。当前 GeoPRR 的数据与逐样本记录见 [全源域结果包](data/geoprr_shared_full_20260911/README.md)；六个基线、保留的适配与变体、α 扫描和效率测量来自 [原实验结果包](data/official_syncg_fulltrain_20260908/README.md)。

直接将本目录整体上传至 Overleaf，并把 `manuscript.tex` 设为 Main document。

目录内容：

- `manuscript.tex`：论文主文件；
- [GeoPRR-Net_中文审阅版V5.9.docx](GeoPRR-Net_中文审阅版V5.9.docx)：与英文稿同步的最新中文审阅源文件，包含结果解读、讨论及模型导向的局限说明；LaTeX 文件为投稿源文件；
- `references.bib`：参考文献；
- `Definitions/`：仓库内的 MDPI *Electronics* 模板文件；
- `figures/`：正文图件、生成图件所用的汇总 CSV 与脚本；图 1 正文直接引用 PNG，中文审阅稿也只引用 PNG。
- `figures/assets/`：图 1 所用公开 RF100-VL 示例 ROI 及其来源说明。
- `data/geoprr_shared_full_20260911/`：新版完整 GeoPRR 的三种子源域及零样本结果；
- `data/official_syncg_fulltrain_20260908/`：原实验的汇总表、训练记录、2,762,352 行逐样本预测及源组统计；
- `data/figure_inputs_shared_full_20260911/`：图 2–5 使用的主比较数据；
- `data/figure_inputs_cross_version_shared_full_20260911/`：表／图 6、7 使用的新参照与保留测量的跨配置比较数据。上述数据不含模型权重、原始工业图像或未匿名化身份。

论文图使用仓库内独立的 `.venv-figures` 环境生成。首次配置及重画命令为：

```bash
python3 -m venv .venv-figures
.venv-figures/bin/python -m pip install -r figures/requirements.txt
.venv-figures/bin/python figures/build_restructured_results.py
```

当前稿件的结果组织：

- 第 5.1 节在官方 SyncG 测试集比较三种 Raw CNN、YOLO、VDN、DeepLab 与 GeoPRR-Net；第 5.2 节在 RF100-VL 和 Industrial-1395 上分别列出同样七个模型的 zero-shot 数据。 两节分别采用直观柱状总览与配对分析图，图注与正文引用同步。
- 主表中的 VDN/DeepLab 使用源域训练的自动参考点；标注辅助结果单独放入附录诊断。
- 第 5.3 节比较新版冻结参照与保留的原配置读出头适配结果：GeoPRR-Net 的六条件 Acc@5% 分别为 51.81% 和 85.15%，NMAE 分别为 11.6235 和 2.4065%FS。图注说明两种配置来源；CNN 保留同一监督与头结构下的匹配对照，三成员集成单独报告。
- 第 3.5 节定义路由增益尺度 α，默认值为 100；第 5.4 节以新版 Full 为参照展示保留变体的差值和置信区间；5.4.1 保留原固定检查点的 α 敏感性图与数据。附录仅保留标注辅助参考诊断。
- 第 5.5 节报告完整读数流水线效率，并单列适配后单成员与三成员集成成本。
- Results 根据图的复杂度解释读数精度、鲁棒性、迁移、适配与资源特点；Discussion 综合模型优势，Limitations 聚焦工业读数精度、预测可信度与完整流程效率。

模板原有的“submitted 日期”和占位 `doi.org` 已通过 `\mdpipublishermetadatafalse` 在作者投稿稿中隐藏，只保留页码。正式 DOI、收稿日期和出版日期由 MDPI 在录用后的制作阶段分配，作者不应自行填写；若编辑部要求恢复模板生产页脚，可将该开关改为 `\mdpipublishermetadatatrue`。

当前作者单位和通讯邮箱按作者要求保留为 University College London 和 `ucabx23@ucl.ac.uk`，正式投稿前仍应向导师或学校确认毕业后的署名许可与邮箱可用性。GeoPRR-Net 的公开代码与复现实验脚本位于 `https://github.com/KongyueX/GeoPRR-Net`，论文源文件、图表和汇总 CSV 位于 `https://github.com/KongyueX/GeoPRR-Net-Paper`。Industrial-1395 使用 1,395 张原生 ROI 和 52 个采集组，分别报告冻结迁移与匹配监督适配；RF100-VL 使用 151 张图、35 个源组及标注导出的归一化目标。官方 SyncG train/test 图像身份互斥但场景身份重叠。全源域结果包与原实验的 details 包共享可连接的样本和分组别名；更早数据包的编号需按各自来源说明处理。原病例图片仍保留在 `selected_cases/`，没有混入当前主实验的图表。
