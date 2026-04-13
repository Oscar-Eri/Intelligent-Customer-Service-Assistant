# API 对接说明

本文档说明如何将前端与你的后端API对接。

## API 配置

在 `src/app/services/chatApi.ts` 中修改以下配置：

```typescript
const API_CONFIG = {
  baseUrl: '/api', // 修改为你的后端API地址，例如 'http://localhost:3000/api'
  endpoints: {
    chat: '/chat', // 普通响应端点
    chatStream: '/chat/stream', // 流式响应端点
  },
};
```

## 响应模式

在 `src/app/App.tsx` 中可以选择使用普通响应或流式响应：

```typescript
const USE_STREAMING = false; // 改为 true 启用流式响应
```

---

## 模式一：普通响应模式

### 后端接口要求

**端点**: `POST /api/chat`

**请求格式**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "你好"
    },
    {
      "role": "assistant",
      "content": "你好！有什么我可以帮助你的吗？"
    },
    {
      "role": "user",
      "content": "介绍一下你自己"
    }
  ]
}
```

**响应格式**:
```json
{
  "message": "我是一个AI助手，可以回答各种问题..."
}
```

或者使用 `content` 字段：
```json
{
  "content": "我是一个AI助手，可以回答各种问题..."
}
```

### 后端示例（Node.js + Express）

```javascript
app.post('/api/chat', async (req, res) => {
  const { messages } = req.body;

  try {
    // 调用你的AI服务
    const aiResponse = await yourAIService.chat(messages);

    res.json({
      message: aiResponse
    });
  } catch (error) {
    res.status(500).json({
      error: error.message
    });
  }
});
```

---

## 模式二：流式响应模式

### 后端接口要求

**端点**: `POST /api/chat/stream`

**请求格式**: 与普通模式相同，但需要额外的 `stream: true` 字段

```json
{
  "messages": [...],
  "stream": true
}
```

**响应格式**: Server-Sent Events (SSE)

响应头：
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

响应体（每个数据块）：
```
data: {"content": "我"}

data: {"content": "是"}

data: {"content": "一个"}

data: {"content": "AI"}

data: {"content": "助手"}

data: [DONE]

```

### 后端示例（Node.js + Express）

```javascript
app.post('/api/chat/stream', async (req, res) => {
  const { messages } = req.body;

  // 设置SSE响应头
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  try {
    // 调用你的AI服务（假设支持流式）
    const stream = await yourAIService.chatStream(messages);

    stream.on('data', (chunk) => {
      // 发送数据块
      res.write(`data: ${JSON.stringify({ content: chunk })}\n\n`);
    });

    stream.on('end', () => {
      // 发送完成信号
      res.write('data: [DONE]\n\n');
      res.end();
    });

    stream.on('error', (error) => {
      res.write(`data: ${JSON.stringify({ error: error.message })}\n\n`);
      res.end();
    });
  } catch (error) {
    res.write(`data: ${JSON.stringify({ error: error.message })}\n\n`);
    res.end();
  }
});
```

---

## 动态修改API配置

如果需要在运行时修改API配置，可以使用 `updateApiConfig` 函数：

```typescript
import { updateApiConfig } from './services/chatApi';

// 修改API地址
updateApiConfig({
  baseUrl: 'https://your-api.com',
  chatEndpoint: '/v1/chat',
  chatStreamEndpoint: '/v1/chat/stream'
});
```

---

## 错误处理

前端会自动处理以下错误情况：

1. 网络错误
2. HTTP错误状态码
3. 响应格式错误
4. 流式响应中断

错误信息会显示在聊天界面中，用户可以重新发送消息。

---

## 跨域配置

如果前后端不在同一域名下，需要在后端配置CORS：

```javascript
// Express 示例
const cors = require('cors');

app.use(cors({
  origin: 'http://localhost:5173', // 你的前端地址
  credentials: true
}));
```

---

## 测试建议

1. 先实现普通响应模式，确保基本功能正常
2. 测试成功后再实现流式响应模式
3. 使用 Postman 或 curl 测试后端接口
4. 检查浏览器控制台的网络请求和错误信息

---

## 常见问题

### 1. 如何添加认证？

在 `chatApi.ts` 中的 `fetch` 调用中添加认证头：

```typescript
headers: {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${yourToken}`,
},
```

### 2. 如何自定义请求/响应格式？

修改 `chatApi.ts` 中的接口函数，调整请求体和响应解析逻辑。

### 3. 流式响应不工作？

- 检查后端是否正确设置了 SSE 响应头
- 确认响应数据格式符合 `data: {...}\n\n` 格式
- 检查浏览器控制台的网络面板，查看实际响应内容
