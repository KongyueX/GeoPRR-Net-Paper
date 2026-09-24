# 补充实验论文结果表

普通结果表为三个独立seed的均值 ± 样本标准差，例如 `0.740 ± 0.022`。06表为三个模型先平均预测、再计算的等权集成结果；13表以“统计方式”区分两者。各表保留六条件总体与逐条件结果。

| 文件 | 内容 |
|---|---|
| [01_E14_完整模型.csv](./01_E14_完整模型.csv) | 独立初始化后的完整模型在三个数据集上的结果。 |
| [02_E27_专家与结构消融.csv](./02_E27_专家与结构消融.csv) | 基础、极坐标、关系专家、简单双视图回归、固定混合与结构移除对照。 |
| [03_E20_路由消融.csv](./03_E20_路由消融.csv) | 完整门控、线性增益头、11标量MLP、三专家等权和固定先验对照。 |
| [04_C4_增强匹配.csv](./04_C4_增强匹配.csv) | 六条件增强Raw EfficientNet-B0与完整模型对照。 |
| [05_C13_目标域OOF.csv](./05_C13_目标域OOF.csv) | Industrial-1395目标监督五折OOF结果。 |
| [06_三模型等权集成.csv](./06_三模型等权集成.csv) | 同一图像同一条件的三个seed模型先平均预测，再计算指标。 |
| [07_E20_路由权重.csv](./07_E20_路由权重.csv) | 三专家平均权重、路由熵与权重集中度。 |
| [08_投影一致性.csv](./08_投影一致性.csv) | 完整模型末端投影均值与路由目标之间的残差。 |
| [09_参数量与延迟.csv](./09_参数量与延迟.csv) | 实际参与模块的参数量与完整ROI读数延迟。 |
| [10_Figure3_六条件.csv](./10_Figure3_六条件.csv) | Figure 3六条件比较及95%置信区间。 |
| [11_Figure3_透视角度.csv](./11_Figure3_透视角度.csv) | 0、15、25、35、45、60度透视扫描及95%置信区间。 |
| [12_Figure3_交互作用.csv](./12_Figure3_交互作用.csv) | 几何融合与自适应路由的NMAE差分之差。 |
| [13_方法差异与置信区间.csv](./13_方法差异与置信区间.csv) | 对照方法减去参考方法的差值及配对bootstrap区间。 |
| [14_Figure3_透视差异.csv](./14_Figure3_透视差异.csv) | 各透视角度下对照方法减去完整模型的差值及95%置信区间。 |

## 指标和单位

- NMAE为平均绝对误差除以满量程，RMSE为均方根误差除以满量程，均以%FS表示。
- Acc@1%、Acc@2%、Acc@5%为误差不超过对应满量程比例的记录占比，单位为%。
- 六条件总体先在每个seed内汇总完整记录，再跨seed求均值与标准差；RMSE从平方误差计算，不直接平均六个条件的RMSE。六条件不作为六倍独立采集样本。
- 95%CI为固定已拟合模型条件下20,000次整组配对bootstrap的点态区间；它与seed间标准差不同。
- 13和14表差值为“对照方法 − 参考方法”；NMAE差值单位为%FS，准确率差值为百分点。
- 12表交互差值为“完整模型 − 固定先验混合 − 去几何融合 + 去几何融合且固定路由”的NMAE差值。
- 07表权重与归一化熵使用0到1尺度，集中度列以%表示；08表残差使用归一化读数尺度，最大值列为各seed最大绝对残差的均值±SD。
- 09表P50/P95是各seed延迟分位数的均值±SD。batch size=1，每seed使用32个预载解码ROI、5次重复；包含SARN、ROI缩放归一化、数据传输与完整读数推理，排除解码、检测与ROI提取。参数量为实际参与模块的独立参数，共享编码器计一次。
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

基础专家读取完整模型的基础候选；简单双视图回归为单独拟合的控制头。05表与06表的“GeoPRR目标监督OOF”使用目标域标签，属于目标监督适配；其他准确率结果为源域训练后的固定模型评测。Figure 3角度扫描的Raw B0为原检查点，C4与六条件表中的Raw B0为六条件增强匹配模型。

## 源统计文件

- 01_E14_完整模型.csv：`syncg/summary.csv；rf100/summary.csv；industrial/summary.csv`。
- 02_E27_专家与结构消融.csv：`syncg/summary.csv；rf100/summary.csv；industrial/summary.csv`。
- 03_E20_路由消融.csv：`syncg/summary.csv；rf100/summary.csv；industrial/summary.csv`。
- 04_C4_增强匹配.csv：`syncg/summary.csv；rf100/summary.csv；industrial/summary.csv`。
- 05_C13_目标域OOF.csv：`adaptation/summary.csv`。
- 06_三模型等权集成.csv：`各数据集summary.csv中的equal_ensemble`。
- 07_E20_路由权重.csv：`routing_seed_mean.csv`。
- 08_投影一致性.csv：`routing_seed_mean.csv`。
- 09_参数量与延迟.csv：`efficiency/summary.csv`。
- 10_Figure3_六条件.csv：`figure3/condition_curves.csv`。
- 11_Figure3_透视角度.csv：`figure3/perspective_curves.csv`。
- 12_Figure3_交互作用.csv：`figure3/geometry_routing_interaction.csv`。
- 13_方法差异与置信区间.csv：`syncg/paired.csv；rf100/paired.csv；industrial/paired.csv`。
- 14_Figure3_透视差异.csv：`figure3/perspective_paired.csv`。

误差保留3位小数，准确率保留2位小数；差值及其区间保留6位小数；投影残差使用科学计数法。CSV采用UTF-8 BOM编码。
