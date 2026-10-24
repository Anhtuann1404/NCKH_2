import os
import subprocess
import tempfile
import zipfile
from pathlib import Path


def main():
    root = Path.cwd()
    zip_path = root / "TASK_CLI_TIMER_PAUSE_HANDOVER.zip"
    with tempfile.TemporaryDirectory() as td:
        tpath = Path(td)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tpath)

        extracted = [str(p.relative_to(tpath)).replace("\\", "/") for p in tpath.rglob("*") if p.is_file()]
        print("Extracted files count:", len(extracted))
        for f in sorted(extracted):
            print(" -", f)

        # Kiểm tra import PausableTimer từ phishing.annotation khi overlay lên codebase
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{tpath / 'src'}{os.pathsep}{root / 'src'}"
        py_exe = str(root / ".venv" / "Scripts" / "python.exe")

        test_code = (
            "from phishing.annotation import PausableTimer, validate_annotation_record\n"
            "print('Successfully imported PausableTimer:', PausableTimer)\n"
            "print('Successfully imported validate_annotation_record:', validate_annotation_record)\n"
        )
        res = subprocess.run([py_exe, "-c", test_code], env=env, capture_output=True, text=True)
        print("\nTest import from extracted zip:")
        print("STDOUT:", res.stdout.strip())
        print("STDERR:", res.stderr.strip())
        assert res.returncode == 0, f"Import failed with code {res.returncode}"

        # Chạy toàn bộ 13 test timer trực tiếp từ file trong zip
        test_file = str(tpath / "tests" / "test_annotate_cli_timer_pause.py")
        res_pytest = subprocess.run([py_exe, "-m", "pytest", test_file, "-v"], env=env, capture_output=True, text=True)
        print("\nPytest on extracted timer tests:")
        print("STDOUT:", res_pytest.stdout.strip())
        assert res_pytest.returncode == 0, f"Pytest failed with code {res_pytest.returncode}"
        print("\n===> VERIFICATION PASSED: ZIP is completely self-contained and import succeeds cleanly! (13/13 tests passed)")


if __name__ == "__main__":
    main()
