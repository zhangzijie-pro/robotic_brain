# Robotic Agent Brain Architecture

一个“基于小型 VLM + 多 Agent + 分层决策”的机器人脑部软件架构。

核心设计文档：

- [docs/multi_agent_vlm_robot_brain_architecture.md](docs/multi_agent_vlm_robot_brain_architecture.md)
- [docs/open_robot_brain_architecture.md](docs/open_robot_brain_architecture.md)
- [docs/project_tree.md](docs/project_tree.md)
- [docs/real_robot_brain_migration.md](docs/real_robot_brain_migration.md)
- [docs/codebase_walkthrough_and_extension_guide.md](docs/codebase_walkthrough_and_extension_guide.md)

## 快速运行

第一次使用时，建议先安装成 editable 包，解决 `ModuleNotFoundError: No module named 'robot_brain'`：

```bash
./scripts/setup_dev_env.sh
```

如果你不想安装包，也可以只在当前 shell 导出：

```bash
export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"
```

建议使用模块方式运行：

```bash
python3 -m robot_brain.demo --pretty
```

默认的机器人执行层是 `dry_run`，只会输出“如果接真机会调用什么”，不会向真实硬件发命令：

```bash
python3 -m robot_brain.demo --pretty --robot-bridge dry_run
```

无人机/巡检类平台可以先用通用 drone profile 看规划自适应效果：

```bash
python3 -m robot_brain.demo --pretty --robot-type drone --robot-bridge dry_run
```

真实机器人接入边界在 `src/robot_brain/control/robot_bridge.py`。可以先切到 ROS2 占位桥查看需要补的 action/service/topic：

```bash
python3 -m robot_brain.demo --pretty --robot-bridge ros2
```

这个模式会 fail closed：没有完成机器人专用 wiring 前会返回失败，不会假装已经控制真机。

不要直接运行包内部文件，例如 `python3 src/robot_brain/agents/vision_agent.py`。这些文件是被包导入的模块，不是独立入口。

默认使用 mock VLM，不需要下载模型：

```bash
./scripts/run_local_demo.sh
```

当前 demo 已经接入一条基础 learning path。输出里除了 `plan` 和 `execution_trace`，还会包含：

- `action_packets`
- `trajectory`
- `learning_records`
- `skill_patches`
- `strategy_snapshot`
- `memory_graph`

如果你希望跨多次运行积累 episodic 经验，可设置：

```bash
export ROBOT_BRAIN_EPISODIC_STORE="$HOME/.robot_brain/episodes.jsonl"
```

使用本机 Ollama：

```bash
ollama pull qwen3.5:0.8b
ollama pull qwen3-vl:2b

ROBOT_BRAIN_VLM_PROVIDER=ollama ./scripts/run_local_demo.sh
```

当前本地 Ollama 默认拆成两条路径：

- text-only dry-run: `qwen3.5:0.8b` + `/api/generate`
- image vision path: `qwen3-vl:2b` + `/api/chat`

已验证可跑通的命令：

```bash
../envirment/bin/python -m robot_brain.demo --provider ollama --pretty
```

如果要让 demo 读取真实图片，请切到视觉模型并提高 image deadline：

```bash
ROBOT_BRAIN_VLM_PROVIDER=ollama \
ROBOT_BRAIN_OLLAMA_VISION_MODEL=qwen3-vl:2b \
ROBOT_BRAIN_VLM_IMAGE_DEADLINE_MS=180000 \
python3 -m robot_brain.demo --provider ollama --image src/robot_brain/img.jpg --pretty
```

注意：`qwen3-vl:2b` 在这台机器上很慢，而且有时只返回 thinking、不返回正文。当前建议先用 text-only Ollama 或 mock 跑通主流程，再把 vision 当成单独实验分支调。

从 Docker 里调用 Mac 宿主机上的 Ollama 时，覆盖 host：

```bash
OLLAMA_HOST=http://host.docker.internal:11434 \
ROBOT_BRAIN_VLM_PROVIDER=ollama \
./scripts/run_local_demo.sh
```

检查当前 Ollama 模型是否能被本机服务调用：

```bash
./scripts/check_ollama_vision.sh
```

运行最小测试：

```bash
PYTHONPATH=src python3 tests/unit/test_world_model.py
PYTHONPATH=src python3 -m unittest discover -s tests
```

当前 demo 不会向真实机器人发送控制命令，只会跑通：

```text
Audio Agent / Vision Agent / Proprioception Agent / Human Interaction Agent
  -> Blackboard
  -> Spatial Agent
  -> World Model
  -> Task Planner
  -> Behavior Planner
  -> Safety Supervisor
  -> Mock Skill Executor
```
