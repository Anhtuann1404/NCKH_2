import { existsSync, statSync } from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

export function pythonPath(project, platform = process.platform, override = process.env.PHISHING_PYTHON) {
  const executable = override || path.join(project, '.venv', ...(platform === 'win32' ? ['Scripts', 'python.exe'] : ['bin', 'python']));
  if (!existsSync(executable) || !statSync(executable).isFile()) {
    throw new Error('Python not found. Create the project .venv or set PHISHING_PYTHON to an executable path (without arguments). See docs/DEVELOPMENT.md.');
  }
  return executable;
}

export function checkedPython(project) {
  const executable = pythonPath(project);
  const result = spawnSync(executable, ['-c', 'import fastapi, uvicorn, numpy, sklearn, joblib'], { encoding: 'utf8' });
  if (result.error || result.status !== 0) {
    throw new Error('Cannot run Python with demo dependencies. Install requirements-dev.lock in the selected environment.');
  }
  return executable;
}
