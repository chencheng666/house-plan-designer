# 增强版架构与数据边界

核心数据流见README的Mermaid图。生成流程需要Agent和本地Python工具，在线页面只提供已经生成的设计器；没有通用AI识图后台。

## 代码分层

- `scripts/analyze.py`、`cadvec.py`、`cadsplit.py`：识别辅助；参考`reference/recognition-workflow.md`核对尺寸链与未知项。
- `examples/d128/spec.json`：可复现公开示例的匿名几何与布置。
- `scripts/build.py`：HouseSpec验证、预设、底图及助手打包。
- `scripts/assistant_bundle.py`：已知模板SHA256、构造器、桥接及分享接口适配保护。
- `assets/template.html`：上游已打包主引擎，包含已验证的PDF与光追补丁。
- `assets/assistant/core.mjs`：几何、多边形、动线、储物、预算、太阳、差异及合并计算。
- `assets/assistant/ui.mjs`：十二页交互、真实模型/贴图、快照与工程包、离线恢复和协作。
- `site/`：静态介绍页、公开Demo与下载入口。

## 保存与迁移

方案数据以毫米为单位，主引擎驱动2D/3D。助手小数据在当前层`plan.enhancements`，大资产及快照在IndexedDB；稳定标识用于跨加载对比。

完整工程包收集当前文档和历史快照实际引用的资产。便携HTML有独立存档键，首次载入内嵌工程，后续保留本机编辑。原生分享转便携时清除旧分享入口，防止旧数据再次导入覆盖新修改。

## 计算范围

动线使用100mm网格和配置净宽；采光与遮挡为简化几何/太阳模型；收纳按明示板厚和尺寸估算；墙面预算为毛面积。价格由用户填写。普通静态GLB/glTF无需远程资源，压缩和骨骼模型需先转换。

本轮仅记录实际macOS Chrome验证结果。原有110项、新增24项、29项程序回归不代表所有浏览器或结构施工验算都已通过。
