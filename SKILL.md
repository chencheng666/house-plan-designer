---
name: house-plan-designer
description: 将户型图片、PDF 或 DXF 还原为离线可用的装修设计器 HTML，支持 2D/3D、家具水电、多楼层、开放分区、动线收纳、预算、真实模型贴图、方案对比和施工协作。适用于户型还原、户型图转 3D、CAD 图纸转装修设计网页；不直接读取 DWG。
---

# 离线户型装修设计器

把户型图片、PDF、DXF还原为单文件HTML，双击离线使用。输出主设计器的2D/3D、家具水电、多层、施工图，以及设计助手2.0的生活需求、开放分区、动线收纳、真实模型贴图、预算、采光、方案对比和施工协作。

## 入口与必读

- **开始还原户型前**：读 [数据格式](reference/spec-format.md) 和 [识别布置流程](reference/recognition-workflow.md)。按图的类型选图片、矢量CAD、整栋楼路线，不能只凭缩略图手写近似墙体。
- **CAD图纸**：再读 [图纸惯例](reference/cad-conventions.md)。
- **多楼层/复式/别墅**：再读 [整栋楼流程](reference/building-workflow.md)。
- **需求/开放分区/收纳/动线/模型材料/报价/对比/协作**：读 [设计助手2.0](reference/assistant-guide.md)。
- **原设计器操作**：按需读 [使用说明](reference/designer-usage.md)；水电规则见 [水电规则](reference/mep-rules.md)。

## 环境

在技能目录执行 `python3 scripts/setup.py`，创建本地`.venv`、安装锁定Python依赖并按锁文件执行`npm ci --ignore-scripts`。要求Python3.12+、Node22.12+、Chrome或Edge；浏览器找不到时设置`CHROME_PATH`。

运行 `python3 scripts/setup.py --check`。下文`python`指`.venv/bin/python`，Windows为`.venv/Scripts/python.exe`，不要安装到系统Python。

## 工作顺序

1. 查看原图及标注，确认尺寸链、门窗类型/开向、房间、结构、层数。DWG不直接读取，先转DXF/SVG或PDF。工作文件放图片旁`<图名>_design/`。
2. 按详细识别流程运行`analyze.py`、`cadvec.py`或`cadsplit.py`，保留识别依据。图片颜色、尺寸链和轴线/墙面基准需要核对；颜色或厚度推测不代表已确认承重。
3. 从识别初稿补齐HouseSpec，优先以图上标注逐段定位。没有尺寸时找已有已知尺寸，否则标明估算；尺寸冲突、设备井和层高/墙厚等未知项保留记录。
4. 按用户要求布置家具、家电和水电，通常启用`autoElec:true`。主箱、弱电箱、管井、下水口、热水器等位置要有依据；改过后再检查。
5. **保留用户确认的结构**。要求书房客厅、厨房家政打通时，取消对应分隔；用助手的开放分区表达功能，不重新加墙、门或玻璃分隔。`material:none`保持连续原铺装。
6. 生成、自查、改错，再执行下方完整验收。资料未提供的家庭人数、城市/纬度/北向、单价等标记为待填写/待核实/待询价，不虚构用户资料或市场报价。

```bash
python scripts/build.py <工作目录>/spec.json -o <图片目录>/<户型名>-装修设计器.html
node scripts/check.mjs <设计器.html> <工作目录>/检查 --strict
```

`--strict`出现警告、错误、丢墙、丢门窗、悬空墙端或房间标签异常时退出2，不能称通过。对原图固有问题可另作非严格诊断并说明例外；不可隐藏或擅自移除原有对象来凑通过。家具重叠、嵌墙、门扇遮挡等原检查器错误/警告应修复；确实属于原图条件的逐项说明。助手的使用空间和采光估算提醒另行复核，不代表施工验算。

`spec`顶层可用固定`projectId`及`assistant`预置功能分区、需求和识别依据，字段见助手说明。助手默认打入单文件，无需服务端。大模型/贴图/截图在IndexedDB，跨设备交付用完整工程包、便携HTML或原生分享HTML，原生JSON不含这些大资产。

## 交付前验收

原有功能和新增功能必须分别通过，报告实际覆盖与跳过项；脚本不删除非空输出目录，始终用新目录。macOS使用Metal、Windows使用D3D11、Linux使用GL；软件渲染的几何检查不能代替真GPU验收。

```bash
node scripts/qa.mjs <设计器.html> <工作目录>/完整验收
python scripts/qa_files.py <工作目录>/完整验收/downloads
node scripts/qa-assistant.mjs <设计器.html> <工作目录>/助手验收
python scripts/qa_files.py <工作目录>/助手验收/downloads
```

- 原有验收110项；助手验收24项，包括真实模型/贴图、预算、快照及冲突合并、批注、跨存储恢复、便携二次编辑保留、原生分享、稳定标识、源修订恢复与窄屏。
- `qa.mjs --quick`跳过PDF/光追；不能称完整验收。`report.json`的`complete/skipped/failed`以真实结果为准。
- 补测用`node scripts/qa-extra.mjs <html> <新目录> --only=kitchen,socket,pdf,pt --pt-complete`，可选择范围；补测不替代其余验收。光追必须验证真实采样、实际下载和图像；自动完成与提前结束分别说明。
- 页面报错、异常数值文字、操作未生效、空白三维或无下载均算失败。验收截图需人工查看，覆盖关键弹窗、方案对比、模型、夜景、桌面和窄屏；PDF逐页渲染看标注可读性。
- 改过原家具库/程序建模时另跑`qa_furniture.mjs`逐件查看。助手自定义模型通过真实网格导入与恢复验收。
- 修改脚本/计算时运行`python -m unittest discover -s scripts/tests -p 'test_*.py'`及`node --test scripts/tests/*.test.mjs`。纯函数测试不能替代浏览器实际交互。

交付提供HTML链接、2D/3D图片、识别与估测说明、真实验收结果及尚待核实事项。源图重建后不自动覆盖旧编辑；助手会保留编辑检查点供比较，重要节点仍下载完整工程包。

## 修改与安装同步

本仓库没有原始TypeScript项目，不能执行不存在的源码构建命令。主模板`assets/template.html`已包含PDF点位说明避让和光追真实计数修复；`scripts/patch_template.py`仅接受已知版本且幂等。

设计助手源码在`assets/assistant/`，构建适配器是`scripts/assistant_bundle.py`，通过唯一接口匹配注入，不修改压缩模板。新增功能优先在该扩展维护；主引擎改动需取得源码或添加明确版本保护及回归的补丁。未知模板接口停止构建，不可禁用助手后宣称升级完成。

同步安装前备份，复制SKILL、reference、assets、scripts、锁定依赖和版本文件，保留安装目录`.venv`与`scripts/node_modules`。重新build、验证安装副本内容及Skill元数据。取得原始引擎源码时才在其项目执行`npm run skill:sync`，随后复核已有补丁、适配器和完整回归。
