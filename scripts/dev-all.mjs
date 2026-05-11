#!/usr/bin/env node

/**
 * dev-all.mjs - 一键启动 Evolith + OpenMAIC 全部服务
 *
 * 用法:
 *   npm run dev:all
 *
 * OpenMAIC 路径按以下顺序查找:
 *   1. 环境变量 OPENMAIC_DIR
 *   2. 项目根 .env 中的 OPENMAIC_DIR
 *   3. 同级目录 ../OpenMAIC (默认约定)
 */

import { spawn } from 'child_process';
import { existsSync, readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { platform } from 'os';

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = resolve(__dirname, '..');
const isWin = platform() === 'win32';

// --- 解析 OpenMAIC 路径 ---
function findOpenmaicDir() {
  if (process.env.OPENMAIC_DIR) return process.env.OPENMAIC_DIR;

  const envFile = resolve(rootDir, '.env');
  if (existsSync(envFile)) {
    const content = readFileSync(envFile, 'utf-8');
    const match = content.match(/^OPENMAIC_DIR\s*=\s*(.+)$/m);
    if (match) return match[1].trim().replace(/^["']|["']$/g, '');
  }

  const defaultPath = resolve(rootDir, '..', 'OpenMAIC');
  if (existsSync(resolve(defaultPath, 'package.json'))) return defaultPath;

  return null;
}

const openmaicDir = findOpenmaicDir();

if (!openmaicDir || !existsSync(resolve(openmaicDir, 'package.json'))) {
  console.error('');
  console.error('  OpenMAIC 未找到。请通过以下方式之一指定路径:');
  console.error('');
  console.error('  1) 设置环境变量:');
  console.error('     set OPENMAIC_DIR=F:\\AI Projects\\OpenMAIC   (Windows CMD)');
  console.error('     export OPENMAIC_DIR=/path/to/OpenMAIC      (bash/zsh)');
  console.error('');
  console.error('  2) 在项目根目录 .env 文件中添加:');
  console.error('     OPENMAIC_DIR=F:\\AI Projects\\OpenMAIC');
  console.error('');
  console.error('  3) 将 OpenMAIC 放在 Evolith 的同级目录 (默认约定)');
  console.error('');
  process.exit(1);
}

console.log('');
console.log('  Evolith + OpenMAIC 全服务启动');
console.log('  ─────────────────────────────');
console.log(`  Backend:   http://localhost:5001`);
console.log(`  Frontend:  http://localhost:3000`);
console.log(`  OpenMAIC:  http://localhost:3001  (${openmaicDir})`);
console.log('');

// --- 带颜色前缀的日志 ---
const colors = { backend: 32, frontend: 36, openmaic: 35 }; // green, cyan, magenta

function prefixLog(name, data) {
  const c = colors[name] || 37;
  const lines = data.toString().split('\n');
  for (const line of lines) {
    if (line.trim()) {
      process.stdout.write(`\x1b[${c}m[${name}]\x1b[0m ${line}\n`);
    }
  }
}

// --- 启动子进程 ---
const children = [];

function startService(name, cmd, args, cwd) {
  const child = spawn(cmd, args, {
    cwd,
    shell: true,
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true,
  });

  child.stdout.on('data', (data) => prefixLog(name, data));
  child.stderr.on('data', (data) => prefixLog(name, data));

  child.on('exit', (code) => {
    const colorCode = colors[name] || 37;
    console.log(`\x1b[${colorCode}m[${name}]\x1b[0m 进程退出 (code=${code})`);
    // 任意一个服务退出，关闭其他所有
    for (const c of children) {
      if (c !== child && !c.killed) {
        c.kill('SIGTERM');
      }
    }
    process.exit(code ?? 0);
  });

  children.push(child);
  return child;
}

// Backend
startService(
  'backend',
  isWin ? 'uv' : 'uv',
  ['run', 'python', 'run.py'],
  resolve(rootDir, 'backend'),
);

// Frontend
startService(
  'frontend',
  isWin ? 'npm' : 'npm',
  ['run', 'dev'],
  resolve(rootDir, 'frontend'),
);

// OpenMAIC
startService(
  'openmaic',
  isWin ? 'npx' : 'npx',
  ['next', 'dev', '--port', '3001'],
  openmaicDir,
);

// --- 优雅关闭 ---
function shutdown() {
  for (const child of children) {
    if (!child.killed) {
      child.kill('SIGTERM');
    }
  }
  process.exit(0);
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
