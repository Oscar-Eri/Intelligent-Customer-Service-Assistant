@echo off
chcp 65001 >nul
echo ========================================
echo RAG 功能集成测试
echo ========================================
echo.

echo [步骤1/3] 安装依赖...
pip install aiofiles tiktoken nest-asyncio
echo.

echo [步骤2/3] 生成知识库摘要...
cd /d "%~dp0"
python backendtest\LLM\RAG\generate_summary.py
echo.

if %errorlevel% neq 0 (
    echo ❌ 知识库摘要生成失败
    pause
    exit /b 1
)

echo [步骤3/3] 运行集成测试...
python tests\test_rag_integration.py
echo.

if %errorlevel% neq 0 (
    echo ❌ 测试失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ 所有测试通过!
echo ========================================
pause
