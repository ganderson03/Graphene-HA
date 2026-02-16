#!/bin/bash
# Build script for Escape Sentinel multi-language analyzer

set -e

echo "╔════════════════════════════════════════════╗"
echo "║   Building Graphene HA                     ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Build Rust orchestrator
echo "🦀 Building Rust orchestrator..."
cargo build --release
echo "✅ Rust orchestrator built"
echo ""

# Build Java bridge
echo "☕ Building Java analyzer bridge..."
if command -v mvn &> /dev/null; then
    cd analyzers/java-bridge
    mvn clean package -q
    cd ../..
    echo "✅ Java bridge built"
else
    echo "⚠️  Maven not found - skipping Java bridge"
fi
echo ""

# Setup Node.js bridge
echo "📦 Setting up Node.js analyzer bridge..."
if command -v node &> /dev/null; then
    cd analyzers/nodejs-bridge
    npm install --silent
    chmod +x analyzer.js
    cd ../..
    echo "✅ Node.js bridge ready"
else
    echo "⚠️  Node.js not found - skipping Node.js bridge"
fi
echo ""

# Build Go bridge
echo "🐹 Building Go analyzer bridge..."
if command -v go &> /dev/null; then
    cd analyzers/go-bridge
    go build -o escape-analyzer main.go
    cd ../..
    echo "✅ Go bridge built"
else
    echo "⚠️  Go not found - skipping Go bridge"
fi
echo ""

# Build Rust bridge
echo "🦀 Building Rust analyzer bridge..."
cd analyzers/rust-bridge
cargo build --release
cd ../..
echo "✅ Rust bridge built"
echo ""

# Build Rust test examples
echo "🧪 Building Rust test examples..."
cd tests/rust
cargo build --release --examples
cd ..
echo "✅ Rust test examples built"
echo ""

# Setup Python bridge
echo "🐍 Setting up Python analyzer bridge..."
if command -v python3 &> /dev/null; then
    chmod +x analyzers/python-bridge/analyzer_bridge.py
    echo "✅ Python bridge ready"
else
    echo "⚠️  Python3 not found - skipping Python bridge"
fi
echo ""

echo "╔════════════════════════════════════════════╗"
echo "║   Build Complete!                          ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "Run './target/release/graphene-ha list' to see available analyzers"
echo "Run './target/release/graphene-ha analyze --help' for usage"
echo ""
