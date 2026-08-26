# ThingLoom

[英文版](README.md)

> **一句话构建你的智能家居。**

ThingLoom 将自然语言需求转化为一条经过验证、真正可运行的链路：从物理传感器到
实时看板。智能体负责指导接线、生成固件、烧录开发板、创建安全消息通道，并在
确认收到真实数据后才宣布项目完成。

## 为什么需要 ThingLoom

即使是一个小型智能家居设备，通常也需要手动拼接开发板驱动、固件、无线网络、
MQTT、TLS、云端凭据和看板。大多数教程在生成代码后就结束了。ThingLoom 将这些
经验封装为可复用的智能体技能，并把**真实硬件产生真实遥测数据**作为完成标准。

目标不是再造一个物联网框架，而是提供从想法到联网设备最短且可靠的路径：

```text
一句话需求
  -> 连接传感器
  -> 生成并烧录固件
  -> 通过安全 MQTT 发布数据
  -> 验证真实消息
  -> 打开实时看板
  -> 存储并分析历史数据（待办）
```

## 尝试一个项目

可以从以下任一经过验证的端到端技能开始：

### 温度与湿度

```sh
git clone https://github.com/emqx/thing-loom.git
cd thing-loom/dht22
codex
```

然后输入：

```text
帮我构建一个温湿度监控器。
```

该技能会完成接线指导、Zero EMQX 创建、固件编译与烧录、MQTT 验证，以及本地或
远程实时看板。硬件和安全细节请查看 [DHT22 项目](dht22/README.md)。

### 环境光

```sh
cd thing-loom/bh1750
codex
```

然后输入：

```text
帮我构建一个环境光监控器。
```

[BH1750FVI 项目](bh1750/README.zh-CN.md)沿用同一条经过验证的完整链路，并以
勒克斯为单位发布真实照度读数。

## 工具链

| 工具 | 作用 |
|---|---|
| 智能体技能 | 将一句话需求转化为可重复执行的硬件流程。 |
| [Arduino CLI](https://arduino.github.io/arduino-cli/) | 编译、烧录并监控 ESP32 固件。 |
| [Zero EMQX](https://zero.emqx.io/) | 创建隔离、一次性使用的 MQTT 命名空间，提供需要认证的 MQTTS 和 WSS 消息传输。 |
| [MQTTX CLI](https://mqttx.app/docs/cli/downloading-and-installation) | 独立验证设备消息是否真正到达 MQTT。 |
| [Cloudflare Workers 静态资源](https://developers.cloudflare.com/workers/static-assets/) | 在需要远程地址时发布实时浏览器看板。 |
| [EMQX Tables](https://docs.emqx.com/zh/cloud/latest/emqx_tables/emqx_tables_overview.html) | **待办：**持久化并查询设备时序数据。 |

## 原则

- 只有真实设备发布了有效读数，生成的项目才算完成。
- 凭据只保存在本地且被 Git 忽略的文件中，绝不输出到聊天或日志。
- Zero EMQX 用于一次性演示；长期运行的智能家居需要持久凭据和存储。
- 先跑通一条完整链路，再构建通用设备框架或扩展大量传感器。

## 路线图

- [x] ESP32-C6 和 DHT22 -> 安全 MQTT -> 实时看板
- [x] ESP32-C6 和 BH1750FVI -> 安全 MQTT -> 实时看板
- [ ] MQTT -> EMQX Tables 时序存储
- [ ] 历史图表、告警和长期运行的智能家居部署
- [ ] 更多经过验证的传感器技能

## 一起创造属于我们的智能世界

每一个经过实机验证的技能，都能把接线、固件、协议和云服务组成的复杂迷宫，变成
一句简单的需求。无论你带来一个传感器、一个想法，还是一条已经跑通的完整链路，
都可以帮助技术少一些配置，多一些创造。

参考[技能贡献模板](examples/README.zh-CN.md)，提交一条由你亲自验证的硬件到看板
完整链路。

> **加入我们，让复杂的工作从一句话开始。**

## 许可证

[MIT](LICENSE)
