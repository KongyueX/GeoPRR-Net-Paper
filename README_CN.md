# GeoPRR-Net / Electronics Overleaf 上传包

直接将本目录整体上传至 Overleaf，并把 `manuscript.tex` 设为 Main document。

目录内容：

- `manuscript.tex`：论文主文件；
- `GeoPRR-Net_中文翻译版.docx`：与正文图片及图注同步的中文审阅译稿，不作为投稿源文件；
- `references.bib`：参考文献；
- `Definitions/`：仓库内的 MDPI *Electronics* 模板文件；
- `figures/`：正文图件、生成图件所用的汇总 CSV 与脚本；图 1 正文直接引用 PNG，中文审阅稿也只引用 PNG。
- `figures/assets/`：图 1 所用公开 RF100-VL 示例 ROI 及其来源说明。
- `data/`：当前公开的 SyncG、RF100-VL、VDN 逐样本预测表，以及新版 Figure 3 的 Geometry × Routing 联合消融和透视角度/fallback 扫描账本、训练历史、详细汇总统计与机器可读清单；不含模型权重、原始图像或 Industrial-1395 私有逐样本记录。

当前稿件已按投稿稿口径完成以下处理：

- VDN 正式比较已替换旧的临时交集结果：每个方法 3 个独立终端检查点，每个种子覆盖 1,558 张图像、6 个条件和 9,348 行；总体 NMAE 为 GeoPRR-Net `1.0013 ± 0.0382 %FS`、VDN `1.6620 ± 0.0878 %FS`，相对降低 39.8%。
- 新增 VDN 三联图，完整展示总体值、六条件值和按 14 个场景聚类的配对 bootstrap 区间；中度透视条件下的无显著差异也被保留。
- 新版 Figure 3 已生成在 `figures/fig3_ablation_routing.{png,pdf}`，并同步到英文主稿和中文审阅译稿的图片及图注；Figure 3a 补齐 Geometry × Routing 四组合，Figure 3e 覆盖 0°、15°、25°、35°、45°、60° 的完整透视与 identity-fallback 扫描。除图注外，正文结果段落保持不变。
- 作者贡献按单作者 CRediT 写法保留；Funding 写为“无外部资助”；Conflicts of Interest 写为“无利益冲突”；伦理和知情同意均说明不适用。
- Data Availability 已写入 SyncG DOI、RF100-VL 真实数据链接、两个 GeoPRR-Net GitHub 地址及已公开的结果账本；Industrial-1395 仅公开统一队列的匿名组级统计，图像和逐样本记录仍说明不能公开再分发的原因与申请方式。
- AI 使用同时在方法部分说明边界，并在 Acknowledgments 中列出 OpenAI Codex、访问时间、作者审阅和责任声明。

模板原有的“submitted 日期”和占位 `doi.org` 已通过 `\mdpipublishermetadatafalse` 在作者投稿稿中隐藏，只保留页码。正式 DOI、收稿日期和出版日期由 MDPI 在录用后的制作阶段分配，作者不应自行填写；若编辑部要求恢复模板生产页脚，可将该开关改为 `\mdpipublishermetadatatrue`。

当前作者单位和通讯邮箱按作者要求保留为 University College London 和 `ucabx23@ucl.ac.uk`，正式投稿前仍应向导师或学校确认毕业后的署名许可与邮箱可用性。GeoPRR-Net 的公开代码与复现实验脚本位于 `https://github.com/KongyueX/GeoPRR-Net`，论文源文件、图表和汇总 CSV 位于 `https://github.com/KongyueX/GeoPRR-Net-Paper`。Industrial-1395 在整篇论文中只作为一个完整的 1,395 图像、六条件、test-only 队列，不包含任何拆分结果。RF100-VL 评测使用 151 张公开测试图像、35 个保守源组和预先由检测标注导出的归一化目标；它被明确限定为外部迁移检查，不作为官方标量读数榜单。VDN 结果明确限定为带标注 pivot 与有序刻度端点的方向组件比较，而不是完整自动端到端系统排名。`research/`、整篇论文的预编译 PDF 和其他编译中间文件均未放入上传包。
