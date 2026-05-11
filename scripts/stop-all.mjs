#!/usr/bin/env node

/**
 * stop-all.mjs - 一键关闭 Evolith + OpenMAIC 全部服务
 *
 * 用法:
 *   npm run stop
 *   node scripts/stop-all.mjs
 *
 * 关闭监听以下端口的所有进程:
 *   3000 - 前端 (Vite)
 *   3001 - OpenMAIC (Next.js)
 *   5001 - 后端 (Flask)
 */

import { execSync } from 'child_process';
import { platform } from 'os';

const isWin = platform() === 'win32';
const PORTS = [
  { port: 3000, name: '前端 (Vite)' },
  { port: 3001, name: 'OpenMAIC' },
  { port: 5001, name: '后端 (Flask)' },
];

function findPidsOnPort(port) {
  if (isWin) {
    try {
      const output = execSync(`netstat -ano | findstr :${port}`, {
        encoding: 'utf-8',
        windowsHide: true,
      });
      const pids = new Set();
      for (const line of output.split('\n')) {
        if (line.includes('LISTENING')) {
          const parts = line.trim().split(/\s+/);
          const pid = parseInt(parts[parts.length - 1], 10);
          if (pid > 0) pids.add(pid);
        }
      }
      return [...pids];
    } catch {
      return [];
    }
  } else {
    try {
      const output = execSync(`lsof -ti :${port}`, { encoding: 'utf-8' });
      return output
        .trim()
        .split('\n')
        .map((p) => parseInt(p, 10))
        .filter((p) => p > 0);
    } catch {
      return [];
    }
  }
}

function killPid(pid) {
  if (isWin) {
    try {
      execSync(`taskkill /PID ${pid} /F`, { windowsHide: true });
      return true;
    } catch {
      return false;
    }
  } else {
    try {
      execSync(`kill -9 ${pid}`);
      return true;
    } catch {
      return false;
    }
  }
}

function isProcessAlive(pid) {
  if (isWin) {
    try {
      const output = execSync(`tasklist /FI "PID eq ${pid}"`, {
        encoding: 'utf-8',
        windowsHide: true,
      });
      return !output.includes('没有找到') && output.includes(pid.toString());
    } catch {
      return false;
    }
  } else {
    try {
      execSync(`kill -0 ${pid}`);
      return true;
    } catch {
      return false;
    }
  }
}

console.log('');
console.log('  Evolith + OpenMAIC 停止所有服务');
console.log('  ──────────────────────────────');
console.log('');

let killedCount = 0;
let alreadyDeadCount = 0;

for (const { port, name } of PORTS) {
  const pids = findPidsOnPort(port);

  if (pids.length === 0) {
    console.log(`  ${name}  (端口 ${port}) - 未运行`);
    continue;
  }

  for (const pid of pids) {
    if (!isProcessAlive(pid)) {
      // TCP 残留条目，进程已不存在
      alreadyDeadCount++;
      continue;
    }

    const success = killPid(pid);
    if (success) {
      console.log(`  ${name}  (端口 ${port}, PID ${pid}) - 已停止`);
      killedCount++;
    } else {
      console.log(`  ${name}  (端口 ${port}, PID ${pid}) - 停止失败`);
    }
  }
}

console.log('');

if (killedCount > 0) {
  console.log(`  已停止 ${killedCount} 个服务进程`);
}

if (alreadyDeadCount > 0) {
  console.log(
    `  ${alreadyDeadCount} 个 TCP 残留条目（进程已不存在，系统将自动回收）`,
  );
}

if (killedCount === 0 && alreadyDeadCount === 0) {
  console.log('  所有服务均未运行，无需停止');
}

console.log('');