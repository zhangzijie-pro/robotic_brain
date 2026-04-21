# 代码导读与扩展指南

这份文档解决四个问题：

1. 现在这套代码到底是怎么跑起来的。
2. 你以后要改功能时，应该改哪一层。
3. 怎么把它从 demo 接到真实机器人系统。
4. 怎么补 skill、底层控制、传感器输入和 RL。

## 1. 先用一句话理解这套工程

它不是“一个大模型直接控机器人”，而是：

```text
多源感知 -> 黑板 -> 世界模型 -> 任务规划 -> 技能执行 -> 机器人桥接层
                         \-> learning / memory / reflection
```

也就是上层负责“理解和决策”，下层负责“可靠执行”。

## 2. 你先看哪些文件

建议按这个顺序看：

- `src/robot_brain/demo.py`
  - 总入口。这里把 Agent、WorldModel、Planner、SkillExecutor、Memory/Reflection 都串起来。
- `src/robot_brain/agents/`
  - 感知入口。把命令、图像、机器人状态、人机状态变成结构化 Fact。
- `src/robot_brain/blackboard/`
  - 共享事实层。所有 Agent 的输出先写到这里。
- `src/robot_brain/brain/world_model.py`
  - 把黑板事实融合成当前世界状态。
- `src/robot_brain/brain/task_planner.py`
  - 根据世界状态生成高层步骤 `PlanStep`。
- `src/robot_brain/skills/`
  - 每个高层动作的实现入口，比如导航、抓取、交接。
- `src/robot_brain/control/robot_bridge.py`
  - 真机接入边界。这里决定最后调用 ROS2/action/service/topic，还是底层驱动。
- `src/robot_brain/vlm_service/providers.py`
  - 模型后端。现在支持 `mock` 和 `ollama`。
- `src/robot_brain/decision_models/`
  - 把 planner step 转成结构化 `ActionPacket`。
- `src/robot_brain/learning/`、`src/robot_brain/memory/`
  - learning path。记录轨迹、总结 lesson、沉淀 procedural / episodic memory。

## 3. 现在一次 demo 是怎么流动的

`demo.py` 里的主流程可以粗看成这样：

1. `AudioAgent` 产生命令事实。
2. `VisionAgent` 产出 `scene_summary`、`object`、`risk`。
3. `ProprioceptionAgent` 产出 `robot_state`。
4. `HumanInteractionAgent` 产出 `human_state`。
5. `SpatialAgent` 给 object 补空间关系和可达性。
6. `WorldModel` 把这些事实融合成一个当前状态。
7. `TaskPlanner` 根据当前状态输出 `PlanStep` 列表。
8. `ParallelActionHead` 把 step 变成 `ActionPacket`。
9. `SafetySupervisor` 决定每一步能不能执行。
10. `SkillExecutor` 按 step.skill 调具体 skill。
11. skill 再调 `RobotBridge`，决定真实要发什么控制命令。
12. learning/memory 记录这次执行，生成 `trajectory`、`learning_records`、`skill_patches`。

## 4. 以后你改东西，应该改哪一层

### 4.1 改“看到了什么”

改这里：

- `src/robot_brain/agents/vision_agent.py`
- `src/robot_brain/agents/proprioception_agent.py`
- `src/robot_brain/agents/human_interaction_agent.py`
- `src/robot_brain/agents/spatial_agent.py`

原则：

- Agent 只负责产出结构化事实。
- 不要在 Agent 里直接做底层控制。
- 不要在 Agent 里塞完整任务逻辑。

### 4.2 改“要做什么”

改这里：

- `src/robot_brain/brain/task_planner.py`
- `src/robot_brain/brain/behavior_planner.py`
- `src/robot_brain/executive/`

原则：

- Planner 只决定步骤序列。
- Safety 只决定是否允许。
- 真正的执行细节留给 skill 和 robot bridge。

### 4.3 改“怎么做”

改这里：

- `src/robot_brain/skills/`
- `src/robot_brain/skills/registry.py`
- `src/robot_brain/control/robot_bridge.py`

原则：

- skill 是高层动作模板。
- bridge 是硬件/中间件适配层。
- 底盘、电机、夹爪、相机、ROS2 action client 都不应该塞进 planner。

### 4.4 改“失败后怎么学”

改这里：

- `src/robot_brain/learning/`
- `src/robot_brain/memory/`
- `src/robot_brain/feedback/failure_taxonomy.py`

原则：

- learning path 不要反过来直接篡改线上控制逻辑。
- 先产出 `LearningRecord` / `SkillPatch` 草案，再决定是否人工接受。

## 5. 现在 Ollama 是怎么接的

当前已经改成两条路径：

### 5.1 text-only dry-run

- 模型：`qwen3.5:0.8b`
- 接口：`/api/generate`
- 关键点：`think=false`

原因：

- 你机器上的 `qwen3.5:0.8b` 走 `/api/chat` 时容易卡在 thinking。
- 改成 `/api/generate` 后可以稳定返回正文 JSON。

### 5.2 vision image path

- 模型：`qwen3-vl:2b`
- 接口：`/api/chat`

现实情况：

- 这个模型在你机器上很慢。
- 它有时会把 token 花在 thinking 上，正文 `content` 为空。
- 所以现在“带图像的真实视觉识别”还不够稳定，适合作为实验路径，不适合作为你当前真机集成的唯一感知链。

## 6. 你现在怎么运行

### 6.1 已验证可跑通的模型路径

```bash
../envirment/bin/python -m robot_brain.demo --provider ollama --pretty
```

或者：

```bash
ROBOT_BRAIN_VLM_PROVIDER=ollama ./scripts/run_local_demo.sh
```

这个路径已经验证能跑通，并且会生成完整的 plan / action_packets / learning_records。

### 6.2 图像路径

```bash
ROBOT_BRAIN_OLLAMA_VISION_MODEL=qwen3-vl:2b \
ROBOT_BRAIN_VLM_IMAGE_DEADLINE_MS=180000 \
../envirment/bin/python -m robot_brain.demo --provider ollama --image src/robot_brain/img.jpg --pretty
```

这个路径目前能完成请求，但你机器上的 `qwen3-vl:2b` 结果不稳定，可能出现 `content` 为空，只剩 thinking 的情况。

所以当前建议是：

- 本地开发和流程联调先用 `mock` 或 text-only Ollama。
- 真图像联调把 vision 当成实验分支单独验证。

## 7. 如何接到真实机器人系统

核心边界是：

- 上层脑：`PlanStep` / `Skill` / `ActionPacket`
- 下层执行：`RobotBridge`

### 7.1 你真正该先改哪几个文件

- `src/robot_brain/control/robot_bridge.py`
- `src/robot_brain/control/interfaces.py`
- `src/robot_brain/agents/proprioception_agent.py`
- `src/robot_brain/agents/spatial_agent.py`

### 7.2 推荐接入顺序

#### 第一步：只接传感器，不接运动

先让这些事实是真实的：

- `robot_state`
- `human_state`
- `object`
- `spatial_relation`
- `reachability`

这一步你要做的是：

- 在 `ProprioceptionAgent` 读真实电池、关节状态、急停、底盘状态。
- 在 `VisionAgent` 传真实图像路径或真实相机帧。
- 在 `SpatialAgent` 用真实深度/点云/TF 算位置和可达性。

只要这一步做好，planner 和 skill 层就开始有真实意义。

#### 第二步：接仿真控制

在 `Ros2RobotBridge` 里把这些函数补上：

- `observe()`
- `navigate_to()`
- `estimate_grasp_pose()`
- `grasp()`
- `handover_to_human()`

建议映射：

- 底盘导航 -> Nav2 `NavigateToPose`
- 抓取位姿 -> perception service / MoveIt planning scene
- 机械臂动作 -> MoveIt 2 action 或 follow_joint_trajectory
- 夹爪 -> gripper action / controller topic

#### 第三步：接真机

保持上层不动，只替换 bridge 内部调用。

你应该让真机接口全部落到 `RobotBridge` 里，而不是散在 planner 或 agent 里。

## 8. 电机、外设、底层控制应该怎么加

### 8.1 最稳妥的分层

```text
TaskPlanner / Skill
    -> RobotBridge
        -> ROS2 action/service/topic 或 SDK
            -> 底层控制器
                -> 电机 / 舵机 / gripper / sensor driver
```

### 8.2 不建议的做法

不要让模型或 skill 直接输出这些东西：

- PWM
- 电机转速
- 关节力矩
- 原始串口指令

这些必须留给底层控制器或中间件。

### 8.3 你要加的真实输入

建议最先补这些输入：

- `base_pose`
- `joint_states`
- `gripper_state`
- `battery`
- `emergency_stop`
- `human_distance`
- `camera frame / depth frame`

它们应该先变成 Fact，再进入 `WorldModel`。

## 9. RL 应该挂在哪

RL 不适合直接替代整个大脑。更合理的是挂在两种位置：

### 9.1 作为 skill 内部策略

例子：

- `grasp` skill 内部调用 RL grasp policy
- `follow_escort` skill 内部调用跟随策略
- `dock_charge` skill 内部调用 docking policy

优点：

- 上层 planner 不变
- 风险集中
- 更容易回滚

### 9.2 作为底层 controller

例子：

- base local planner
- arm closed-loop servo policy
- visual servoing

优点：

- 上层继续输出结构化目标
- RL 只负责局部闭环控制

### 9.3 不建议

不要让 RL 直接吃自然语言然后输出电机命令。

那样会把：

- 语言理解
- 高层决策
- 安全约束
- 低层控制

全部耦在一起，几乎没法调试。

## 10. 如何新增一个 skill

假设你要加一个 `open_drawer`。

### 10.1 新建 skill 类

在 `src/robot_brain/skills/` 新增文件，比如：

- `open_drawer.py`

结构参考现有 skill：

```python
class OpenDrawerSkill:
    name = "open_drawer"
    default_risk = "high"

    async def run(self, step: PlanStep, robot_bridge: RobotBridge) -> dict:
        return await robot_bridge.open_drawer(
            drawer_id=str(step.args.get("drawer_id", "unknown")),
            args=step.args,
        )
```

### 10.2 注册 skill

改：

- `src/robot_brain/skills/registry.py`

把它加进 `default_skills()`。

### 10.3 补 robot bridge 能力

改：

- `src/robot_brain/control/robot_bridge.py`

给 `RobotBridge` 协议、`DryRunRobotBridge`、`Ros2RobotBridge` 都加 `open_drawer()`。

### 10.4 让 planner 会用它

改：

- `src/robot_brain/brain/task_planner.py`

根据场景条件输出：

```python
PlanStep(
    name="open_target_drawer",
    skill="open_drawer",
    args={"drawer_id": "..."},
    risk="high",
)
```

### 10.5 补测试

至少补：

- skill executor 能 dispatch 到它
- dry_run bridge 返回正确 envelope
- planner 在正确条件下会生成这个 step

## 11. 如果你要接 ROS2，建议的落地方式

最稳的是在 `Ros2RobotBridge` 里持有这些客户端：

- Nav2 action client
- MoveIt action / service client
- gripper controller client
- perception pose service client
- TTS client

你的 `RobotBridge` 方法只负责：

1. 组装目标参数。
2. 调 ROS2 接口。
3. 返回结构化执行结果。

不要在 bridge 里再写一套高层任务规划。

## 12. 现在最值得你优先做的事

按优先级建议：

1. 先把 `ProprioceptionAgent` 和 `SpatialAgent` 换成真实输入。
2. 把 `Ros2RobotBridge.navigate_to()` 接到底盘仿真。
3. 把 `estimate_grasp_pose()` 接到你的目标位姿估计服务。
4. 把 `grasp()` 接到 MoveIt / 机械臂轨迹控制。
5. 新增你需要的 skill，而不是让 planner 写死越来越多分支。
6. 最后再扩 learning / memory，让失败经验真正回灌。

## 13. 你现在看代码时的心智模型

你可以一直记住下面这句：

- Agent 负责“看到什么”
- WorldModel 负责“现在是什么状态”
- Planner 负责“下一步做什么”
- Skill 负责“这个动作的标准接口”
- RobotBridge 负责“最后怎么控真机”
- Learning/Memory 负责“这次跑完学到了什么”

只要你按这个边界扩展，代码不会越改越乱。
