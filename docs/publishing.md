# 公开版发布

本仓库增强版默认分支为`enhanced-v2`。Fork中的`main`保留上游历史，主模板更新需先通过已知哈希和适配器复核。

## 制作文件

```bash
.venv/bin/python scripts/build.py examples/d128/spec.json -o site/demo/index.html
cp site/demo/index.html site/downloads/d128-designer.html
.venv/bin/python scripts/package_public.py --out artifacts/public-release --release 2.0.0-20261110
```

Skill包只包含运行源码、锁定依赖说明和必要文档，排除本机环境、验收临时目录、文章后台数据。站点包包含逐文件SHA256清单。

## 当前腾讯云环境

`deploy_site.py`针对维护者已有Nginx环境，为`/house-plan-designer/`增加独立路由，目录在`/opt/house-plan-designer`。它不适合作为任意服务器通用脚本直接执行；其他环境可直接部署`site/`静态文件。

脚本以共享发布锁防止并发；验证包摘要与文件路径；备份并原子切换自己的版本链接；仅配置变化时平滑重载Nginx；对原路由、版本指针、页面和两项游戏服务做前后比较。失败只回退本次新站发布。

运行方式：

```bash
python3 deploy_site.py --archive 站点发行包.tar.gz --sha256 发行包SHA256 --release 2.0.0-20261110
```

上线后还需从公网逐文件下载校验，并在真实浏览器验证主页、Demo关键操作及下载。不能用脚本退出成功或HTTP200替代功能验证。

## 公众号

`docs/wechat-v2-20261110/`保存正文与配图排版源。图像来自真实设计器输出；架构图为说明图。草稿的编辑器链接含账号会话参数，不放入公开仓库。文章正文包含GitHub、项目主页与Demo地址，阅读原文指向项目主页。
