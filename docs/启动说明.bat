@echo off
chcp 65001 >nul
echo ====================================
echo Figma AI Chat - 完整项目说明
echo ====================================
echo.
echo 本项目包含前端和后端两个部分
echo.
echo 前端技术栈:
echo   - React + TypeScript
echo   - Vite 6.x
echo   - TailwindCSS 4.x
echo   - Material-UI
echo.
echo 后端技术栈:
echo   - FastAPI
echo   - Python 3.x
echo   - 通义千问 API
echo.
echo ====================================
echo 启动步骤:
echo ====================================
echo.
echo 第一步：启动后端服务
echo   1. 打开一个新的命令行窗口
echo   2. 运行：backend\start.bat
echo   3. 等待看到 "应用已启动" 消息
echo   4. 后端地址：http://localhost:8000
echo.
echo 第二步：启动前端服务
echo   1. 在当前目录（frontend）下
echo   2. 确保已安装 Node.js 依赖
echo   3. 运行：npm run dev
echo   4. 前端地址：http://localhost:5173
echo.
echo ====================================
echo 注意事项:
echo ====================================
echo   - 必须先启动后端，再启动前端
echo   - 确保端口 8000 和 5173 未被占用
echo   - 后端需要配置有效的 API Key
echo.
echo ====================================

pause
