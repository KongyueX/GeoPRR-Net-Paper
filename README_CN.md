# GeoPRR-Net / Electronics Overleaf 上传包

直接将本目录整体上传至 Overleaf，并把 `manuscript.tex` 设为 Main document。

目录内容：

- `manuscript.tex`：论文主文件；
- `GeoPRR-Net_中文翻译版V4.2.docx`：与正文图片及图注同步的中文审阅译稿，不作为投稿源文件；小规模改动递增小版本号，较大更新再递增主版本号，当前版本为 V4.2；
- `references.bib`：参考文献；
- `Definitions/`：仓库内的 MDPI *Electronics* 模板文件；
- `figures/`：正文图件、生成图件所用的汇总 CSV 与脚本；图 1 正文直接引用 PNG，中文审阅稿也只引用 PNG。
- `figures/assets/`：图 1 所用公开 RF100-VL 示例 ROI 及其来源说明。
- `data/`：当前公开的 SyncG、RF100-VL、VDN 逐样本预测表、完整 3×4 结构化读数器汇总表、匿名化的 Industrial-1395 适配 OOF 逐行预测，以及新版 Figure 3 的 Geometry × Routing 联合消融和透视角度/fallback 扫描账本、训练历史、详细汇总统计与机器可读清单；不含模型权重、原始图像或未匿名化的 Industrial-1395 来源记录。

当前稿件已按投稿稿口径完成以下处理：

- 表 8 已更新为三个数据集 × 四种方法的完整矩阵：GeoPRR-Net、VDN、DeepLabV3+-ROI 和 YOLO11s-Pose-4KP 均覆盖 SyncG、Industrial-1395 与 RF100-VL 的六条件清单；GeoPRR-Net 在三个域上均取得最低汇总 NMAE。
- 图 6 已扩展为 NMAE 与 Acc@5 的 2×3 绝对性能矩阵；新增图 7 展示相对 NMAE 降幅、Acc@5 百分点增益和输出覆盖率。Industrial-1395 的 GeoPRR-Net 使用有监督五折 OOF 三编码器等权集成，NMAE 为 `2.3262 %FS`、Acc@5% 为 `86.99%`。
- 新版 Figure 3 已生成在 `figures/fig3_ablation_routing.{png,pdf}`，并同步到英文主稿和中文审阅译稿的图片及图注；Figure 3a 补齐 Geometry × Routing 四组合，Figure 3e 覆盖 0°、15°、25°、35°、45°、60° 的完整透视与 identity-fallback 扫描。正文结果段落同步补充了 Figure 3a 的预先指定交互效应及 95% CI。
- 作者贡献按单作者 CRediT 写法保留；Funding 写为“无外部资助”；Conflicts of Interest 写为“无利益冲突”；伦理和知情同意均说明不适用。
- Data Availability 已写入 SyncG DOI、RF100-VL 真实数据链接、两个 GeoPRR-Net GitHub 地址及已公开的结果账本；Industrial-1395 公开统一队列的匿名组级统计和适配 OOF 逐行预测，原始图像与未匿名化来源记录仍说明不能公开再分发的原因与申请方式。
- AI 使用同时在方法部分说明边界，并在 Acknowledgments 中列出 OpenAI Codex、访问时间、作者审阅和责任声明。

模板原有的“submitted 日期”和占位 `doi.org` 已通过 `\mdpipublishermetadatafalse` 在作者投稿稿中隐藏，只保留页码。正式 DOI、收稿日期和出版日期由 MDPI 在录用后的制作阶段分配，作者不应自行填写；若编辑部要求恢复模板生产页脚，可将该开关改为 `\mdpipublishermetadatatrue`。

当前作者单位和通讯邮箱按作者要求保留为 University College London 和 `ucabx23@ucl.ac.uk`，正式投稿前仍应向导师或学校确认毕业后的署名许可与邮箱可用性。GeoPRR-Net 的公开代码与复现实验脚本位于 `https://github.com/KongyueX/GeoPRR-Net`，论文源文件、图表和汇总 CSV 位于 `https://github.com/KongyueX/GeoPRR-Net-Paper`。Industrial-1395 比较使用完整的 1,395 图像、六条件统一队列，GeoPRR-Net 数值采用有监督五折 OOF 目标域适配与三编码器等权集成，不发布来源拆分统计。RF100-VL 评测使用 151 张公开测试图像、35 个保守源组和预先由检测标注导出的归一化目标，并作为外部迁移检查。VDN 与 DeepLabV3+-ROI 在 SyncG 和 RF100-VL 上使用标注导出的表盘几何，在 Industrial-1395 上使用自动估计几何；YOLO11s-Pose-4KP 在三个域上均预测四个几何点。`research/`、整篇论文的预编译 PDF 和其他编译中间文件均未放入上传包。
