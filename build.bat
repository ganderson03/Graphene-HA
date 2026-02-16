@echo off
REM Build script for Graphene HA multi-language analyzer (Windows)

echo ╔════════════════════════════════════════════╗
echo ║   Building Graphene HA                     ║
echo ╚════════════════════════════════════════════╝
echo.

REM Build Rust orchestrator
echo 🦀 Building Rust orchestrator...
cargo build --release
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Rust build failed
    exit /b 1
)
echo ✅ Rust orchestrator built
echo.

REM Build Java bridge
echo ☕ Building Java analyzer bridge...
where mvn >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    cd analyzers\java-bridge
    call mvn clean package -q
    cd ..\..
    echo ✅ Java bridge built
) else (
    echo ⚠️  Maven not found - skipping Java bridge
)
echo.

REM Setup Node.js bridge
echo 📦 Setting up Node.js analyzer bridge...
where node >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    cd analyzers\nodejs-bridge
    call npm install --silent
    cd ..\..
    echo ✅ Node.js bridge ready
) else (
    echo ⚠️  Node.js not found - skipping Node.js bridge
)
echo.

REM Build Go bridge
echo 🐹 Building Go analyzer bridge...
where go >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    cd analyzers\go-bridge
    go build -o escape-analyzer.exe main.go
    cd ..\..
    echo ✅ Go bridge built
) else (
    echo ⚠️  Go not found - skipping Go bridge
)
echo.

REM Build Rust bridge
echo 🦀 Building Rust analyzer bridge...
cd analyzers\rust-bridge
cargo build --release
cd ..\..
echo ✅ Rust bridge built
echo.

REM Build Rust test examples
echo 🧪 Building Rust test examples...
cd tests\rust
cargo build --release --examples
cd ..
echo ✅ Rust test examples built
echo.

REM Python bridge (no build needed)
echo 🐍 Setting up Python analyzer bridge...
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Python bridge ready
) else (
    echo ⚠️  Python not found - skipping Python bridge
)
echo.

echo ╔════════════════════════════════════════════╗
echo ║   Build Complete!                          ║
echo ╚════════════════════════════════════════════╝
echo.
echo Run 'target\release\graphene-ha.exe list' to see available analyzers
echo Run 'target\release\graphene-ha.exe analyze --help' for usage
echo.

pause
