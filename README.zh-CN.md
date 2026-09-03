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

## 开始前的准备

准备一块 ESP32 开发板、DHT22、BH1750FVI 或 SEN0193 等受支持的传感器、USB 数据线和杜邦线，
再连接到可用的 2.4 GHz 无线网络，就可以开始。快速体验或轻量级长期项目可以选择
Zero EMQX，也可以连接已有的 MQTT Broker。如需带 SLA 的服务，可以前往
[EMQX Cloud 创建 Serverless 或 Dedicated Flex 部署](https://www.emqx.com/en/cloud)。

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

该技能会完成接线指导、Broker 配置、固件编译与烧录、MQTT 验证，以及本地或
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

### 土壤湿度

```sh
cd thing-loom/sen0193
codex
```

然后输入：

```text
帮我构建一个土壤湿度监控器。
```

[SEN0193 项目](sen0193/README.zh-CN.md)以毫伏值校准模拟传感器，将读数转换为相对湿度百分比，
并在看板中说明换算方法。

## 工具链

| 工具 | 作用 |
|---|---|
| 智能体技能 | 将一句话需求转化为可重复执行的硬件流程。 |
| [Arduino CLI](https://arduino.github.io/arduino-cli/) | 编译、烧录并监控 ESP32 固件。 |
| [EMQX Cloud](https://www.emqx.com/en/cloud) | 在没有自有 Broker 时创建托管的 Serverless 或 Dedicated Flex 部署。 |
| [Zero EMQX](https://zero.emqx.io/) | 创建隔离的 MQTT 命名空间，提供需要认证的 MQTTS 和 WSS 消息传输；可长期运行，但不提供 SLA。 |
| [MQTTX CLI](https://mqttx.app/docs/cli/downloading-and-installation) | 独立验证设备消息是否真正到达 MQTT。 |
| [Cloudflare Workers 静态资源](https://developers.cloudflare.com/workers/static-assets/) | 在需要远程地址时发布实时浏览器看板。 |
| [EMQX Tables](https://www.emqx.com/en/cloud/emqx-tables) | **待办：**持久化、查询并可视化设备时序数据。 |

## 从第一条读数走向长期智能家居

Zero EMQX 可以支持长期运行的设备，并非只能用于短期演示。使用默认的 `idle_ttl`
生命周期时，只要设备或看板保持连接，命名空间就会一直保留；只有所有客户端断开并
超过创建时返回的空闲时长后才会删除。该服务不提供 SLA，因此适合原型、个人项目和
非关键的长期部署，不适合要求可用性承诺的业务。

当设备需要 SLA、确定的生产容量，或不依赖活跃连接的生命周期时，请使用自己的
Broker，或前往 [EMQX Cloud 创建部署](https://www.emqx.com/en/cloud)。
可以选择 **Serverless**，以按使用量计费的方式快速起步；也可以选择
**Dedicated Flex**，获得专属资源、更高性能和企业级能力。随后使用 EMQX Tables 在
同一个托管平台中保存 MQTT 遥测数据，用于历史查询、分析和可视化。

## 原则

- 只有真实设备发布了有效读数，生成的项目才算完成。
- 凭据只保存在本地且被 Git 忽略的文件中，绝不输出到聊天或日志。
- 先跑通一条完整链路，再构建通用设备框架或扩展大量传感器。

## 路线图

- [x] ESP32-C6 和 DHT22 -> 安全 MQTT -> 实时看板
- [x] ESP32-C6 和 BH1750FVI -> 安全 MQTT -> 实时看板
- [x] ESP32-C6 和 SEN0193 -> 安全 MQTT -> 校准后的实时看板
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
