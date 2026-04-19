# 从 Demo 迁移到真实机器人大脑

这套工程现在是一个安全的机器人脑原型：它会跑完整个认知链路，但默认不会向真实机器人发送控制命令。要变成真实机器人大脑，关键不是把 VLM 换成更大的模型，而是把“感知、世界模型、规划、安全、执行”每一层都接到可验证的机器人接口。

## 现在代码在做什么

当前链路如下：

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

核心文件：

- `src/robot_brain/demo.py`：把所有模块串起来的入口。
- `src/robot_brain/vlm_service/providers.py`：VLM 后端，当前支持 `mock` 和 `ollama`。
- `src/robot_brain/agents/vision_agent.py`：把图像输入转成对象、场景、风险等结构化事实。
- `src/robot_brain/blackboard/event_bus.py`：多 Agent 共享事实的内存黑板。
- `src/robot_brain/brain/world_model.py`：把黑板事实融合成当前世界状态。
- `src/robot_brain/brain/task_planner.py`：把用户目标拆成技能步骤。
- `src/robot_brain/brain/safety_supervisor.py`：在执行前做安全否决。
- `src/robot_brain/skills/executor.py`：把技能步骤分发给机器人桥接层。
- `src/robot_brain/control/robot_bridge.py`：真实机器人硬件/中间件的适配边界。

## 新增的真实化接口

`SkillExecutor` 现在不直接假装执行动作，而是调用 `RobotBridge`：

```python
executor = SkillExecutor(robot_bridge=create_robot_bridge("dry_run"))
```

可选桥接：

- `dry_run`：默认值，只记录“会调用什么硬件能力”，不会发控制命令。
- `ros2`：真实机器人占位桥。它会 fail closed，也就是在你没有写入机器人专用 ROS2 action/service/topic 前直接失败，不会静默假执行。

运行：

```bash
python3 -m robot_brain.demo --pretty --robot-bridge dry_run
```

查看 ROS2 桥接还缺什么：

```bash
python3 -m robot_brain.demo --pretty --robot-bridge ros2
```

它会在 `execution_trace` 里返回失败原因和准备好的 command envelope。

## 接真机的推荐顺序

### 1. 先接真实感知，不接运动

目标：让黑板和世界模型消费真实传感器，但机器人不动。

要做：

- 相机：把 RGB/depth 图像保存成关键帧路径，传给 `VisionAgent(image_refs=[...])`。
- 机器人状态：把真实 `joint_states`、电池、电机状态、急停状态接进 `ProprioceptionAgent`。
- 人体距离：用深度相机、人体检测或安全雷达更新 `HumanInteractionAgent` 的 `distance_m`。
- 坐标系：让 `SpatialAgent` 使用真实 TF/depth/点云，而不是固定 `[0.7, 0.0, 0.78]`。

验收标准：

- `world_model.objects` 里能看到真实物体。
- `world_model.robot_state.emergency_stop` 能反映真实急停。
- `world_model.human_state.distance_m` 能随人靠近而变化。
- 不启动任何运动控制器。

### 2. 再接仿真执行

目标：让 `RobotBridge` 调用仿真里的 Nav2、MoveIt 2、夹爪控制器。

要改：

- 在 `Ros2RobotBridge.navigate_to()` 中创建 Nav2 `NavigateToPose` action client。
- 在 `Ros2RobotBridge.estimate_grasp_pose()` 中把对象位姿写入 MoveIt planning scene，或调用你的抓取位姿服务。
- 在 `Ros2RobotBridge.grasp()` 中调用 MoveIt pick/place 或机械臂轨迹 action。
- 在 `Ros2RobotBridge.handover_to_human()` 中移动到交接位姿，并使用力控/限速释放夹爪。

验收标准：

- `--robot-bridge ros2` 在仿真中能完成 `observe -> navigate -> estimate_grasp -> grasp -> handover`。
- 安全失败时，`SkillResult.status == "failed"` 或 `SafetyDecision.allowed == False`，不能继续执行后续步骤。
- 所有真实/仿真动作都有超时。

### 3. 最后接真机

目标：只替换底层桥接，不改变上层脑结构。

上线顺序：

1. 只读传感器。
2. 底盘低速移动，机械臂禁用。
3. 机械臂空载移动，夹爪禁用。
4. 夹爪抓取软物体。
5. 人机交接，但必须有人类确认。

真机模式建议强制保留：

- 物理急停。
- 软件急停。
- 最大底盘速度限制。
- 最大机械臂速度缩放。
- 人类距离阈值。
- 高风险技能二次确认。
- 控制命令日志。
- 任务失败后的恢复策略。

## 让它更像“大脑”的下一步

当前世界模型还很轻量，下一步可以补这些能力：

- 对象实体绑定：同一个杯子在多帧里保持同一个 ID。
- 空间语义地图：对象、房间、桌面、可达区域都进地图。
- 任务状态机：每个任务有 `pending/running/succeeded/failed/recovering`。
- 记忆系统：保存成功抓取姿态、失败原因、用户偏好。
- 反思 Agent：每次失败后生成可回滚的配置建议，而不是直接改策略。
- 评估集：固定一批场景图像和任务命令，防止 prompt 或模型升级导致退化。

## 真实机器人不要让 VLM 直接控制

VLM 应该输出结构化观察和解释，不应该直接输出电机命令。推荐边界是：

```text
VLM: "红杯子在桌面右侧，靠近桌边，置信度 0.86"
Planner: "需要抓取红杯子"
Safety: "桌边风险存在，允许低速接近，抓取前复查"
RobotBridge: "调用 Nav2 / MoveIt / gripper action"
Controller: "执行轨迹、速度、力矩闭环"
```

这样做的好处是：模型可以不完美，但控制链路仍然可测、可限速、可审计、可急停。
