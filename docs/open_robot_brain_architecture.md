# 开源通用机器人大脑软件架构

目标：把本项目从单一 demo 扩展成可适配移动机器人、机械臂、复合机器人、无人机和自定义平台的“大脑层”。底层控制、驱动和硬件能力由配置与桥接层注入，上层感知、世界模型、认知 Agent、执行管理和反馈学习保持机器人无关。

## 分层结构

```text
Multimodal Sensors
  -> Perception and Preprocessing
  -> World Model and Memory
  -> Cognitive Agents
  -> Executive Layer
  -> Skill Layer
  -> Control Execution Layer
  -> Feedback Loop
```

对应代码目录：

```text
src/robot_brain/
  sensors/       RGB/Depth/LiDAR/Mic/IMU/Force/Tactile 等传感器适配
  perception/    检测、跟踪、姿态、ASR、SLAM、状态估计、安全监控
  world/         World State Blackboard、Scene Graph、Task Context
  memory/        Episodic、Semantic、User Profile 记忆
  cognitive/     任务解析、场景推理、规划、技能路由、安全审查、对话、反思学习
  executive/     仲裁、模式管理、重规划、调度、失败恢复
  skills/        导航、操作、跟随、巡检、人机交互、回充、无人机飞行技能
  control/       底盘、机械臂、夹爪、TTS、ROS2 Action/Service/Topic 接口
  feedback/      执行反馈、失败日志、奖励信号、记忆更新、离线学习
  models/        LLM/VLM 统一模型网关，支持本地、云端、自定义 HTTP
```

## 机器人适配原则

不同机器人不要改 Agent 主逻辑，而是通过 `RobotProfile` 描述能力：

- `robot_type`：例如 `mobile_manipulator`、`drone`、`quadruped`、`custom`。
- `capabilities`：机器人能做什么，例如 `navigate_to`、`grasp`、`fly_to`。
- `sensors`：传感器类型、坐标系、数据来源。
- `control`：ROS2 namespace、controller、action、service、topic 名称。
- `limits`：速度、力、距离、高度、确认条件等安全边界。

示例配置在 `configs/robot_profiles.yaml`。当前代码也提供了内置默认：

```bash
PYTHONPATH=src python3 -m robot_brain.demo --pretty
PYTHONPATH=src python3 -m robot_brain.demo --pretty --robot-type drone
```

默认移动机械臂会规划：

```text
observe -> navigate_to -> estimate_grasp_pose -> grasp -> handover_to_human
```

无人机会规划：

```text
observe -> fly_to -> inspection
```

## 模型服务策略

模型统一走 `src/robot_brain/models/`：

- `mock`：本地测试，不需要模型。
- `ollama`：本地 LLM/VLM。
- `openai_compatible`：云端或自部署 OpenAI-compatible `/v1/chat/completions` 接口。
- `custom_http`：自定义 HTTP 服务，建议保持同样消息结构。

环境变量：

```bash
ROBOT_BRAIN_MODEL_PROVIDER=ollama
ROBOT_BRAIN_OLLAMA_MODEL=qwen3-vl:2b

ROBOT_BRAIN_MODEL_PROVIDER=openai_compatible
ROBOT_BRAIN_MODEL_BASE_URL=https://api.example.com/v1
ROBOT_BRAIN_MODEL_API_KEY=...
ROBOT_BRAIN_MODEL_NAME=your-model
```

旧的 `vlm_service/` 仍保留，确保已有 demo 和 VLM Agent 不被破坏。后续可以逐步把 Agent 迁移到 `ModelGateway`。

## Skill 标准模板

每个技能只表达机器人无关的意图：

```python
class NavigationSkill:
    name = "navigate_to"
    default_risk = "medium"

    async def run(self, step, robot_bridge):
        return await robot_bridge.navigate_to(
            location_hint=step.args["location_hint"],
            args=step.args,
        )
```

真实硬件细节放进 `RobotBridge`：

```python
async def navigate_to(self, location_hint: str, args: dict) -> dict:
    # 这里接 Nav2 NavigateToPose、厂商 SDK、无人车接口等
    ...
```

这样同一个 `NavigationSkill` 可以服务不同平台：

- ROS2 移动底盘：调用 Nav2。
- 仓储 AGV：调用厂商导航 API。
- 四足机器人：调用 waypoint SDK。
- 无人机：使用 `DroneFlyToSkill` 调用飞控 waypoint action。

## 真机上线建议

1. 先接传感器，只读不动。
2. 在仿真中接控制桥，确认失败会停止执行链。
3. 真机低速运行底盘，机械臂禁用。
4. 机械臂空载，夹爪禁用。
5. 夹爪抓取软物体。
6. 人机交互动作必须保留确认、限速、急停和日志。

VLM/LLM 永远不要直接输出电机命令。模型输出结构化事实和候选计划，安全层与控制层负责可验证执行。
