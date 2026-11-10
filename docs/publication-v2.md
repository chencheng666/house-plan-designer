# 2.0 公开发布与验收记录

2026年11月10日发布。源码、离线文件和在线示例均已开放；公众号文章保存为草稿，尚未发表。

## 公开入口

- 源码：https://github.com/chencheng666/house-plan-designer （默认分支 `enhanced-v2`）
- 发行版：https://github.com/chencheng666/house-plan-designer/releases/tag/v2.0.0
- 项目主页：https://www.daguojueqi.site/house-plan-designer/
- 户型 Demo：https://www.daguojueqi.site/house-plan-designer/demo/
- 文章网页预览：https://www.daguojueqi.site/house-plan-designer/article.html

发行版保留上游 MIT 许可与署名。`main` 保留上游历史，增强版在 `enhanced-v2`。`v2.0.0` 对应发行源码提交 `7b9ec0a240474c59c6da0ad790bdda6227c30b2e`；后续验收文档提交不移动标签，也不替换已发布附件。

## 站点与实际功能

- 腾讯云独立目录与路由原子发布，15个公开文件全部通过公网逐文件 SHA256 校验。
- 正式切换事务前后，7个原站页面摘要、原站配置、游戏版本指针与两项游戏服务状态一致。只为新路由平滑重载 Nginx，没有重启原游戏服务。
- 主页真实点击下载离线 HTML，下载摘要与发行文件一致；主页桌面图片正常、无横向溢出。
- 在线 Demo 实际切换 3D，导入并放置静态 GLB 网格，导出32页 PDF。
- 在线 Demo 光追完成20次真实采样，手动结束后保存1920×1080 PNG；以上浏览器路径未出现脚本错误或 CSP 违规。
- 本机完整光追按120秒时限自动保存，完成168次采样。文章展示的是这张完整输出；线上20次采样用于验证部署后的运行和保存链路，两者分别记录。
- 本地公开示例新增24项交互验证全部通过；原功能110项、新增功能24项、Python13项与Node19项回归的结果保留在功能验收记录中。
- 根目录及 Demo 内不存在的 JS 文件均返回404。

复核站点时，使用部署事务报告中的 `before` 快照与发行包 `manifest.json`：

```bash
python3 scripts/verify_site.py \
  --manifest 发行目录/manifest.json \
  --before 本地部署事务报告.json \
  --out 本地公网验收报告.json
```

部署报告、后台编辑链接及临时预览链接只保存在维护者本地，不进入公开仓库。

## 发行附件摘要

| 文件 | SHA256 |
| --- | --- |
| house-plan-designer-site-v2.0.0.tar.gz | `7eddd6835ef048535a4fc9269b61914204e4a9fb49ac70b15fb12bf55b2956ef` |
| house-plan-designer-skill-v2.0.0.zip | `ea242379f2645efe1a8bf02e240f0babb574742a7653694304956694faa5d955` |
| d128-designer.html | `de7c776d8713eb42c0de9d626d05f48f0c8c8e112d611f7b8b228e2d36bf2923` |
| d128-drawings.pdf | `65a68f3dbe0e13f4121aac5be807448ebc572ff17b5cc488d60d143b7ed61117` |

## 公众号材料

账号：数字机器莱西奥。作者：陈成。

标题：**把户型图变成可编辑的3D家：我给开源装修设计器做了一次升级**。

正文介绍功能、适用价值、实际架构、直接试用与 Skill 使用方法，包含 GitHub、主页、Demo 和上游地址。封面1张、正文配图5张，均已通过原生上传进入微信素材服务；图像来自设计器实际输出，架构图为说明图。

草稿已手动保存并重新打开回读；正文、封面、作者、摘要、AI标识和阅读原文链接均保留。手机宽390px预览无横向溢出，滚动后5张正文图片全部加载。公众号草稿尚未发表，公开的 `article.html` 仅为网站上的文章预览。

文章与图片源文件见 [公众号材料目录](wechat-v2-20261110/)。辅助计算、施工复核与跨平台验收边界在文章及 README 中分别说明。
