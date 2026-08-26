# 贡献 ThingLoom 技能

[英文版](README.md)

一项贡献应该让一个真实设备走完整条经过验证的链路。只生成文件并不算完成：硬件
必须产生有效读数，最终使用方也必须收到数据。

## 从模板开始

在仓库根目录运行：

```sh
cp -R examples/skill-template my-sensor
mv my-sensor/SKILL.md.tmpl my-sensor/SKILL.md
mv my-sensor/README.md.tmpl my-sensor/README.md
mv my-sensor/README.zh-CN.md.tmpl my-sensor/README.zh-CN.md
mv my-sensor/agents/openai.yaml.tmpl my-sensor/agents/openai.yaml
mv my-sensor/.gitignore.tmpl my-sensor/.gitignore
```

替换所有 `REPLACE_ME`，然后删除技能不需要的可选文件或章节。

## 推荐目录结构

```text
my-sensor/
├── SKILL.md                 必需的智能体说明
├── README.md                英文用户指南
├── README.zh-CN.md          中文用户指南
├── .gitignore               保护本地输出和凭据
├── agents/
│   └── openai.yaml          可选的界面元数据
├── scripts/                 可选的确定性工具和一个小型测试
├── assets/                  可选的项目模板和接线图
├── references/              可选且按需读取的说明
└── data/                    被忽略的本地输出，禁止提交凭据
```

技能格式只要求提供 `SKILL.md`。其他目录只有在实现确实需要时才添加。

## 提交检查

- 技能名和目录名使用小写字母与连字符，长度不超过 64 个字符。
- 在文件头说明技能具体做什么，以及什么情况下应该使用。
- 完整指导一条真实硬件链路，并定义可以观察的完成证据。
- 复用已有代码和工具，只安装缺少的依赖。
- 禁止在聊天、日志、提交文件和字面命令文本中出现密码或 Token；优先使用隐藏提示或受保护的配置文件。
- 网络凭据和遥测数据必须通过需要认证的加密连接传输。
- 脚本包含非简单逻辑时，添加一个小型离线测试。
- 不要提交生成项目和构建产物。
- 中英文用户指南保持内容一致。
- 提交前检查暂存差异中没有凭据，然后运行新增测试和 `git diff --check`。

[DHT22 技能](../dht22/)是第一个完整示例。
