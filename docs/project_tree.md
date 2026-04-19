# 工程骨架 Tree 与模块讲解

## 当前目录

```text
robotic_agent/
  configs/
    agents.yaml
    model_service.yaml
    robot_profiles.yaml
    safety_limits.yaml
    skills.yaml
    vlm_service.yaml
  docs/
    multi_agent_vlm_robot_brain_architecture.md
    open_robot_brain_architecture.md
    project_tree.md
    real_robot_brain_migration.md
    vlm_recommendations.md
  src/robot_brain/
    sensors/       多模态传感器适配模板
    perception/    感知与预处理节点模板
    world/         黑板、场景图、任务上下文
    memory/        情景、语义、用户偏好记忆
    cognitive/     任务解析、推理、规划、安全审查、对话、反思学习 Agent
    executive/     仲裁、模式、调度、重规划、失败恢复
    skills/        标准机器人无关技能模板与注册表
    control/       ROS2/硬件/控制器桥接边界
    feedback/      执行反馈、失败日志、奖励信号、离线学习
    models/        LLM/VLM 统一模型网关
    agents/        兼容旧 demo 的感知 Agent
    brain/         兼容旧 demo 的世界模型、规划和安全层
    blackboard/    内存黑板
    vlm_service/   兼容旧 demo 的 VLM 服务
```

## 正式架构链路

```text
Sensors
  -> Perception
  -> World Model / Memory
  -> Cognitive Agents
  -> Executive Layer
  -> Skill Layer
  -> Control Layer
  -> Feedback Loop
```

## 兼容链路

当前 `python3 -m robot_brain.demo --pretty` 仍会跑旧 demo 链路：

```text
AudioAgent / VisionAgent / ProprioceptionAgent / HumanInteractionAgent
  -> Blackboard
  -> SpatialAgent
  -> WorldModel
  -> TaskPlanner
  -> BehaviorPlanner
  -> SafetySupervisor
  -> SkillExecutor
  -> RobotBridge
```

不同点是：`SkillExecutor` 已经改成标准技能注册表，执行时会调用 `RobotBridge`，而不是在执行器里写死技能逻辑。
