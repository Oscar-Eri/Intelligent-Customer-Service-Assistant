# MemoryManager - 记忆管理模块（增强版）

## 📋 功能特性

### 核心功能
- ✅ **对话历史管理**：存储、检索、清理对话消息
- ✅ **Token 控制**：自动截断超出限制的对话
- ✅ **长期记忆**：将重要对话总结并保存到文件
- ✅ **跨会话记忆**：程序重启后仍能记住之前的对话内容
- ✅ **智能总结**：使用 LLM 自动生成对话摘要

### 新增功能（相比原版）
1. **持久化存储**：通过 JSON 文件保存对话总结
2. **自动加载**：启动时自动加载之前的记忆
3. **上下文注入**：在新对话中自动包含历史总结
4. **手动控制**：支持手动保存、加载、清空记忆

---

## 🚀 快速开始

### 基础用法

```python
import asyncio
from backend.LLM.Memory.memory_manager import create_memory_manager

async def main():
    # 创建记忆管理器
    memory = create_memory_manager(
        max_tokens=4000,
        memory_file="my_memory.json"  # 指定记忆文件路径
    )
    
    # 添加对话
    memory.add_user_message("我想买智能手表")
    memory.add_ai_message("我们有 SW-1300、SW-1500、SW-1800 等型号")
    
    # 生成总结（保存到长期记忆）
    summary = await memory.generate_summary()
    print(f"总结：{summary}")
    
    # 获取用于 LLM 的消息（包含历史总结）
    messages = memory.get_messages_for_llm()
    
    # 查看记忆状态
    status = memory.get_memory_status()
    print(status)

asyncio.run(main())
```

---

## 📖 API 文档

### 初始化参数

```python
MemoryManager(
    max_tokens: int = 4000,      # 最大 token 数限制
    max_messages: Optional[int] = None,  # 最大消息数量
    memory_file: Optional[str] = None,   # 长期记忆文件路径
    enable_summary: bool = True          # 是否启用总结功能
)
```

### 主要方法

#### 1. 消息管理
- `add_user_message(content: str)` - 添加用户消息
- `add_ai_message(content: str)` - 添加 AI 回复
- `get_messages()` - 获取所有消息
- `get_messages_for_llm(include_summary=True)` - 获取传递给 LLM 的消息（可包含历史总结）
- `clear()` - 清空当前对话（保留长期记忆）
- `clear_all()` - 清空所有记忆（包括长期记忆）

#### 2. 长期记忆
- `generate_summary(force=False)` - 生成对话总结（异步方法）
- `save_memory()` - 手动保存到文件
- `load_memory()` - 从文件加载记忆
- `get_memory_status()` - 获取记忆状态信息

#### 3. 工具方法
- `get_message_count()` - 获取消息数量
- `estimate_tokens()` - 估算 token 数
- `get_last_message()` - 获取最后一条消息
- `get_conversation_summary()` - 获取对话摘要（调试用）

---

## 💡 使用场景

### 场景 1：跨会话记忆

```python
# 第一次会话
memory1 = create_memory_manager(memory_file="user_001.json")
memory1.add_user_message("我喜欢运动风格的手表")
memory1.add_ai_message("推荐 SW-1500 Sport 运动版")
await memory1.generate_summary()  # 保存记忆

# 第二次会话（程序重启）
memory2 = create_memory_manager(memory_file="user_001.json")
# 自动加载了之前的记忆
print(memory2._conversation_summary)  
# 输出："用户喜欢运动风格的手表，已推荐 SW-1500 Sport"

# 继续对话，AI 会记得用户的偏好
memory2.add_user_message("还有其他推荐吗？")
messages = memory2.get_messages_for_llm()  # 包含历史总结
```

### 场景 2：定期总结

```python
# 在对话过程中定期生成总结
for i in range(10):
    memory.add_user_message(f"问题{i}")
    memory.add_ai_message(f"回答{i}")
    
    # 每 5 轮对话生成一次总结
    if i % 5 == 0:
        await memory.generate_summary()
```

### 场景 3：多用户记忆

```python
# 为不同用户创建不同的记忆文件
def get_user_memory(user_id: str):
    return create_memory_manager(
        memory_file=f"memories/user_{user_id}.json"
    )

# 用户 A
user_a_memory = get_user_memory("alice")
user_a_memory.add_user_message("我是 Alice")

# 用户 B
user_b_memory = get_user_memory("bob")
user_b_memory.add_user_message("我是 Bob")

# 各自的记忆独立保存
```

---

## 🔧 高级配置

### 自定义总结触发条件

```python
memory = create_memory_manager(
    max_tokens=4000,
    memory_file="memory.json"
)

# 手动控制总结生成
if memory.get_message_count() > 10:  # 超过 10 条消息才总结
    await memory.generate_summary()
```

### 禁用总结功能

```python
# 如果不需要长期记忆，可以禁用总结
memory = create_memory_manager(
    enable_summary=False  # 禁用总结
)
```

### 自定义 LLM 配置

修改 `memory_manager.py` 中的 LLM 配置：

```python
self.llm = ChatOpenAI(
    model="qwen-plus",      # 修改模型
    base_url=qwen_base_url,
    api_key=qwen_api_key,
    temperature=0.3,        # 调整温度（0-1，越低越稳定）
)
```

---

## 📊 记忆文件格式

记忆文件是 JSON 格式：

```json
{
  "summary": "用户喜欢运动风格的手表，预算 1000 元左右，已推荐 SW-1500 Sport 运动版",
  "last_updated": "E:\\QRTlongchaintraining\\PROJ\\AIchat\\backendtest"
}
```

---

## 🧪 测试和示例

### 运行测试
```bash
cd E:\QRTlongchaintraining\PROJ\figma测试\backend
python LLM/Memory/test_memory.py
```

### 运行示例
```bash
python LLM/Memory/example_usage.py
```

---

## ⚠️ 注意事项

1. **异步方法**：`generate_summary()` 是异步方法，需要使用 `await` 调用
2. **文件路径**：确保 `memory_file` 的目录存在，或程序有权限创建
3. **Token 限制**：总结会自动控制在 200 字以内
4. **错误处理**：总结生成失败不会影响现有记忆
5. **性能考虑**：频繁调用 `generate_summary()` 会增加 API 调用次数

---

## 🔄 与原有代码的兼容性

完全兼容原有接口，以下代码无需修改：

```python
# 旧代码仍然可用
memory = MemoryManager(max_tokens=4000)
memory.add_user_message("你好")
messages = memory.get_messages()
```

新功能是**可选的**，只需添加 `memory_file` 参数即可启用：

```python
# 启用长期记忆
memory = MemoryManager(
    max_tokens=4000,
    memory_file="memory.json"  # 添加这行即可
)
```

---

## 📝 最佳实践

1. **在合适时机生成总结**
   - 对话结束时
   - 达到一定消息数量时
   - 用户离开页面时

2. **合理设置记忆文件**
   - 按用户 ID 分开存储
   - 定期清理过期记忆
   - 使用有意义的文件名

3. **性能优化**
   - 不要每条消息都触发总结
   - 批量处理多条消息后再生成总结
   - 考虑缓存机制

---

## 🛠️ 故障排除

### 问题 1：记忆文件未创建
**原因**：没有调用 `generate_summary()` 或 `save_memory()`
**解决**：确保在适当时机调用保存方法

### 问题 2：总结为空
**原因**：消息太少（少于 4 条）
**解决**：使用 `force=True` 参数强制生成

### 问题 3：记忆未加载
**原因**：文件路径错误或文件不存在
**解决**：检查 `memory_file` 路径是否正确

---

## 📚 相关文件

- `memory_manager.py` - 核心实现
- `test_memory.py` - 测试文件
- `example_usage.py` - 使用示例
- 本文件 - 使用说明

---

## 🎯 未来计划

- [ ] 支持多种记忆格式（摘要、关键词、时间线）
- [ ] 支持记忆压缩和归档
- [ ] 支持记忆检索和查询
- [ ] 支持分布式记忆存储
- [ ] 支持记忆版本控制

---

**更新时间**：2026-03-19  
**版本**：v2.0 (增强版)
