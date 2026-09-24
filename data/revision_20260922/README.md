# 补充实验论文结果表

数据集中在一个文件：[supplementary_experiment_results.csv](./supplementary_experiment_results.csv)。文件按实验纵向分区，每区使用自身的指标表头，最多9列；用Excel打开CSV即可在一张工作表中阅读全部结果。

普通结果为三个独立seed的均值 ± 样本标准差，例如 `0.740 ± 0.022`。常规精度、消融、OOF、投影残差、交互作用及方法差异均取六条件总体。仅Figure 3条件曲线和SyncG完整模型路由随条件变化保留六条件明细；透视曲线与透视差异保留各扫描角度。

“三模型等权集成”为三个模型先平均预测、再计算指标；“方法差异与置信区间”区以“统计方式”区分均值与集成结果。

| 实验分区 | 内容 |
|---|---|
| E14 完整模型｜六条件总体 | 独立初始化后的完整模型在三个数据集上的结果。 |
| E27 专家与结构消融｜六条件总体 | 基础、极坐标、关系专家、简单双视图回归、固定混合与结构移除对照。 |
| E20 路由消融｜六条件总体 | 完整门控、线性增益头、11标量MLP、三专家等权和固定先验对照。 |
| C4 增强匹配｜六条件总体 | 六条件增强Raw EfficientNet-B0与完整模型对照。 |
| C13 目标域OOF｜六条件总体 | Industrial-1395目标监督五折OOF结果。 |
| 三模型等权集成｜六条件总体 | 同一图像同一条件的三个seed模型先平均预测，再计算指标。 |
| E20 路由权重 | 三专家平均权重、路由熵与权重集中度。 |
| 投影一致性｜六条件总体 | 完整模型末端投影均值与路由目标之间的残差。 |
| 参数量与延迟 | 实际参与模块的参数量与完整ROI读数延迟。 |
| Figure3 六条件｜SyncG | Figure 3六条件比较及95%置信区间。 |
| Figure3 透视角度｜SyncG | 0、15、25、35、45、60度透视扫描及95%置信区间。 |
| Figure3 交互作用｜SyncG｜六条件总体 | 几何融合与自适应路由的NMAE差分之差。 |
| 方法差异与置信区间｜六条件总体 | 对照方法减去参考方法的差值及配对bootstrap区间。 |
| Figure3 透视差异｜SyncG | 各透视角度下对照方法减去完整模型的差值及95%置信区间。 |

## 指标和单位

- NMAE为平均绝对误差除以满量程，RMSE为均方根误差除以满量程，均以%FS表示。
- Acc@1%、Acc@2%、Acc@5%为误差不超过对应满量程比例的记录占比，单位为%。
- 六条件总体先在每个seed内汇总完整记录，再跨seed求均值与标准差；RMSE从平方误差计算，不直接平均六个条件的RMSE。六条件不作为六倍独立采集样本。
- 95%CI为固定已拟合模型条件下20,000次整组配对bootstrap的点态区间；它与seed间标准差不同。
- 方法差异与透视差异为“对照方法 − 参考方法”；NMAE差值单位为%FS，准确率差值为百分点。
- 交互差值为“完整模型 − 固定先验混合 − 去几何融合 + 去几何融合且固定路由”的NMAE差值。
- 路由权重与归一化熵使用0到1尺度，集中度列以%表示；投影残差使用归一化读数尺度，最大值列为各seed最大绝对残差的均值±SD。
- P50/P95是各seed延迟分位数的均值±SD。batch size=1，每seed使用32个预载解码ROI、5次重复；包含SARN、ROI缩放归一化、数据传输与完整读数推理，排除解码、检测与ROI提取。参数量为实际参与模块的独立参数，共享编码器计一次。
- 本批准确率表覆盖率均为100%；效率测量失败调用均为0。

## 方法

- GeoPRR完整模型：`full`。
- 仅几何/基础专家：`base_only`。
- 简单双视图回归：`dual_view`。
- 仅极坐标专家：`polar_only`。
- 仅关系专家：`relational_only`。
- 去几何融合：`no_geometry_fusion`。
- 去几何融合+固定路由：`no_geometry_fixed_routing`。
- 去关系传输：`no_relational_transport`。
- 去极坐标证据：`no_polar_evidence`。
- 线性增益头：`linear_gate`。
- 11标量MLP门控：`scalar_gate`。
- 三专家等权混合：`uniform`。
- 固定先验混合：`fixed_prior`。
- Raw B0（六条件增强）：`raw_efficientnet_b0_six_condition`。
- Raw B0（原检查点）：`raw_efficientnet_b0`。
- GeoPRR目标监督OOF：`geoprr_oof`。

基础专家读取完整模型的基础候选；简单双视图回归为单独拟合的控制头。“GeoPRR目标监督OOF”及对应集成结果使用目标域标签，属于目标监督适配；其他准确率结果为源域训练后的固定模型评测。Figure 3角度扫描的Raw B0为原检查点，C4与六条件曲线中的Raw B0为六条件增强匹配模型。

## 源统计文件

- E14 完整模型｜六条件总体：`syncg/summary.csv；rf100/summary.csv；industrial/summary.csv`。
- E27 专家与结构消融｜六条件总体：`syncg/summary.csv；rf100/summary.csv；industrial/summary.csv`。
- E20 路由消融｜六条件总体：`syncg/summary.csv；rf100/summary.csv；industrial/summary.csv`。
- C4 增强匹配｜六条件总体：`syncg/summary.csv；rf100/summary.csv；industrial/summary.csv`。
- C13 目标域OOF｜六条件总体：`adaptation/summary.csv`。
- 三模型等权集成｜六条件总体：`各数据集summary.csv中的equal_ensemble`。
- E20 路由权重：`routing_seed_mean.csv`。
- 投影一致性｜六条件总体：`routing_seed_mean.csv`。
- 参数量与延迟：`efficiency/summary.csv`。
- Figure3 六条件｜SyncG：`figure3/condition_curves.csv`。
- Figure3 透视角度｜SyncG：`figure3/perspective_curves.csv`。
- Figure3 交互作用｜SyncG｜六条件总体：`figure3/geometry_routing_interaction.csv`。
- 方法差异与置信区间｜六条件总体：`syncg/paired.csv；rf100/paired.csv；industrial/paired.csv`。
- Figure3 透视差异｜SyncG：`figure3/perspective_paired.csv`。

误差保留3位小数，准确率保留2位小数；差值及其区间保留6位小数；投影残差使用科学计数法。CSV采用UTF-8 BOM编码。
