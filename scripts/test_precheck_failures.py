#!/usr/bin/env python3
"""
可重复的发布前检查失败场景测试脚本

验证 pre_release_check.py 在以下场景下返回非 0 退出码：
1. dist 目录缺失
2. 版本不一致 (gw_dsl_parser)

运行方式：
    python scripts/test_precheck_failures.py
"""

import sys
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "pre_release_check.py"
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
DIST_DIR = PROJECT_ROOT / "pygwalker" / "templates" / "dist"


def run_precheck():
    """运行预检查，返回 (exit_code, output)"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--skip-import", "--verbose"],
        env=env,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    return result.returncode, result.stdout + result.stderr


def test_dist_missing():
    """测试 1: dist 目录缺失时返回非 0"""
    print("\n" + "=" * 70)
    print("TEST 1: 验证 dist 目录缺失时返回非 0")
    print("=" * 70)
    
    # 检查 dist 目录是否存在
    if not DIST_DIR.exists():
        print("[SKIP] dist 目录不存在，无法测试")
        return True
    
    # 保存 dist 目录
    backup_dir = DIST_DIR.with_name("dist_backup_test")
    
    try:
        # 移动 dist 目录
        print(f"  -> 移动 dist 目录到 {backup_dir.name}")
        shutil.move(str(DIST_DIR), str(backup_dir))
        
        # 运行预检查
        print("  -> 运行预检查...")
        exit_code, output = run_precheck()
        
        # 验证结果
        if exit_code != 0:
            print(f"  ✓ [PASS] 检查失败，退出码: {exit_code}")
            if "dist directory not found" in output:
                print("  ✓ [PASS] 错误信息包含 'dist directory not found'")
                return True
            else:
                print(f"  ✗ [FAIL] 错误信息不匹配: {output[-200:]}")
                return False
        else:
            print(f"  ✗ [FAIL] 检查应该失败但返回了退出码 0")
            print(f"  输出: {output[-500:]}")
            return False
    
    finally:
        # 恢复 dist 目录
        if backup_dir.exists():
            print(f"  -> 恢复 dist 目录")
            shutil.move(str(backup_dir), str(DIST_DIR))


def test_version_mismatch():
    """测试 2: gw_dsl_parser 版本不一致时返回非 0"""
    print("\n" + "=" * 70)
    print("TEST 2: 验证 gw_dsl_parser 版本不一致时返回非 0")
    print("=" * 70)
    
    # 备份原始 pyproject.toml
    backup_content = PYPROJECT_PATH.read_text()
    
    try:
        # 修改版本（改为不匹配的值）
        original_line = 'gw_dsl_parser==0.1.49.1'
        modified_line = 'gw_dsl_parser==0.1.99.0'
        
        print(f"  -> 修改版本: {original_line} -> {modified_line}")
        modified_content = backup_content.replace(original_line, modified_line)
        PYPROJECT_PATH.write_text(modified_content)
        
        # 验证修改成功
        if modified_line not in PYPROJECT_PATH.read_text():
            print("  ✗ [FAIL] 无法修改 pyproject.toml")
            return False
        
        # 运行预检查
        print("  -> 运行预检查...")
        exit_code, output = run_precheck()
        
        # 验证结果
        if exit_code != 0:
            print(f"  ✓ [PASS] 检查失败，退出码: {exit_code}")
            if "versions mismatch" in output:
                print("  ✓ [PASS] 错误信息包含 'versions mismatch'")
                return True
            else:
                print(f"  ✗ [FAIL] 错误信息不匹配: {output[-200:]}")
                return False
        else:
            print(f"  ✗ [FAIL] 检查应该失败但返回了退出码 0")
            print(f"  输出: {output[-500:]}")
            return False
    
    finally:
        # 恢复原始 pyproject.toml
        print("  -> 恢复 pyproject.toml")
        PYPROJECT_PATH.write_text(backup_content)


def test_success_case():
    """测试 3: 正常情况返回 0"""
    print("\n" + "=" * 70)
    print("TEST 3: 验证正常情况返回 0")
    print("=" * 70)
    
    print("  -> 运行预检查...")
    exit_code, output = run_precheck()
    
    if exit_code == 0:
        print(f"  ✓ [PASS] 检查通过，退出码: {exit_code}")
        if "All pre-checks passed" in output:
            print("  ✓ [PASS] 包含成功信息 'All pre-checks passed'")
            return True
        else:
            print(f"  ✗ [FAIL] 成功信息不匹配: {output[-200:]}")
            return False
    else:
        print(f"  ✗ [FAIL] 检查应该通过但返回了退出码 {exit_code}")
        print(f"  输出: {output[-500:]}")
        return False


def main():
    print("\n" + "#" * 70)
    print("# 发布前检查失败场景测试")
    print("#" * 70)
    
    results = []
    
    # 测试 1: 成功场景
    results.append(("成功场景", test_success_case()))
    
    # 测试 2: dist 缺失
    results.append(("dist 缺失", test_dist_missing()))
    
    # 测试 3: 版本不一致
    results.append(("版本不一致", test_version_mismatch()))
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status:12} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "-" * 70)
    passed_count = sum(1 for _, p in results if p)
    failed_count = len(results) - passed_count
    print(f"  结果: {passed_count} passed, {failed_count} failed")
    print("=" * 70)
    
    if all_passed:
        print("\n  [✓] 所有测试通过！预检查机制可以正确拦住发布问题。")
        return 0
    else:
        print("\n  [✗] 部分测试失败，请检查问题。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
