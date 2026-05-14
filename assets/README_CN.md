# Assets 资源文件夹

## 简介

本文件夹包含 LLMRouter 项目所需的所有静态资源文件，包括项目 Logo、示意图、演示动画和视频等。

## 文件夹作用

`assets/` 文件夹用于存放项目相关的视觉资源文件，这些资源主要用于：

- 项目文档和 README 中的说明插图
- 网站和界面的展示材料
- 演示和教程的动态展示
- 品牌标识和项目形象展示

## 文件类型列表

| 文件类型 | 说明 |
|---------|------|
| PNG 图片 | 高质量静态图片，用于 Logo、示意图等 |
| JPG 图片 | 压缩图片，用于展示图等 |
| GIF 动图 | 动态演示图，用于展示功能流程 |
| MOV 视频 | 高清演示视频，用于完整功能演示 |

## 资源用途说明

### Logo 相关

- **logo.png** - 项目主要 Logo 图标
- **logo_claw.png** - 带有爪子元素的项目 Logo 变体

### LLMRouter 示意图

- **llmrouter.jpg** - LLMRouter 项目主展示图（JPG 格式）
- **llmrouter_.png** - LLMRouter 项目主展示图（PNG 格式，高清）
- **llmrouter_new.png** - LLMRouter 新版本示意图
- **llmrouter_new_.png** - LLMRouter 新版本示意图（另一变体）
- **llmrouter_old.png** - LLMRouter 旧版本示意图（用于版本对比）
- **llmrouter_notext.png** - LLMRouter 示意图（不带文字版本）
- **llmrouter_with_text_v2.png** - LLMRouter 示意图（带文字 v2 版本）
- **llmrouter_with_text_v3.png** - LLMRouter 示意图（带文字 v3 版本）

### 演示资源

- **llmrouter_chat.gif** - LLMRouter 聊天功能动态演示（GIF 动图）
- **llmrouter_chat_demo.mov** - LLMRouter 聊天功能完整演示视频（MOV 格式）

### ComfyUI 相关

- **comfyui.png** - ComfyUI 相关的示意图

## 使用指南

### 在文档中使用

在 Markdown 文档中引用资源时，使用相对路径：

```markdown
![LLMRouter 示意图](./assets/llmrouter.png)
```

### 在代码中使用

在 HTML 或代码中引用资源时，同样使用相对路径：

```html
<img src="assets/logo.png" alt="LLMRouter Logo">
```

### 资源选择建议

- **文档插图**：推荐使用 PNG 格式（如 `llmrouter_.png`），保证清晰度
- **网页展示**：可使用 JPG 格式（如 `llmrouter.jpg`），文件更小
- **功能演示**：使用 GIF 动图（如 `llmrouter_chat.gif`），轻量级展示
- **完整演示**：使用 MOV 视频（如 `llmrouter_chat_demo.mov`），展示完整流程
- **品牌展示**：使用 Logo（如 `logo.png` 或 `logo_claw.png`）

## 注意事项

1. 请勿随意删除或重命名这些资源文件，可能导致文档或演示失效
2. 添加新资源时，请遵循现有的命名规范
3. 建议优先使用 PNG 格式以保持图片质量
4. 大型视频文件（如 MOV）请谨慎使用，注意加载性能