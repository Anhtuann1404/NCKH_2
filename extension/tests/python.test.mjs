import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { pythonPath } from './python.mjs';

test('Python selection supports Windows, POSIX, explicit paths and missing environments', () => {
  const project = mkdtempSync(path.join(tmpdir(), 'nckh-python-'));
  try {
    for (const parts of [['bin', 'python'], ['Scripts', 'python.exe']]) {
      const executable = path.join(project, '.venv', ...parts);
      mkdirSync(path.dirname(executable), { recursive: true });
      writeFileSync(executable, 'fixture, not executable');
    }
    assert.equal(pythonPath(project, 'win32', ''), path.join(project, '.venv', 'Scripts', 'python.exe'));
    assert.equal(pythonPath(project, 'darwin', ''), path.join(project, '.venv', 'bin', 'python'));
    const custom = path.join(project, 'custom python');
    writeFileSync(custom, 'fixture');
    assert.equal(pythonPath(project, 'win32', custom), custom);
    assert.throws(() => pythonPath(project, 'win32', path.join(project, 'missing')), /Python not found/);
    assert.throws(() => pythonPath(project, 'win32', project), /Python not found/);
  } finally { rmSync(project, { recursive: true, force: true }); }
});
