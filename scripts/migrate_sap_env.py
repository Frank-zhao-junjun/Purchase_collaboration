"""将 Integration/user.txt 中的 SAP 密码迁移到 gitignore 的 backend/.env。

安全说明（SEC-005）：
- 不再使用明文凭证文件读取密码，密码改为经由环境变量 SAP_COMM_PASSWORD 注入。
- 本脚本仅做一次性迁移：读取 user.txt -> 写入 .env -> 删除 user.txt。
- 脚本不向 stdout 输出任何密码明文。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER_TXT = ROOT / "Integration" / "user.txt"
ENV = ROOT / "backend" / ".env"


def parse_password(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        # 支持 "password:xxx" 或 "password：xxx"（全角冒号）
        m = re.match(r"^\s*password\s*[:：]\s*(.+?)\s*$", line, re.IGNORECASE)
        if m:
            return m.group(1)
    raise ValueError("未在 user.txt 中找到 password 行")


def main() -> None:
    if not USER_TXT.exists():
        print("[skip] user.txt 不存在，无需迁移")
        return

    password = parse_password(USER_TXT)

    # 构造新的 .env：保留非 SAP_CREDENTIALS_FILE 行，覆盖 SAP_COMM_PASSWORD
    lines = []
    seen_pw = False
    if ENV.exists():
        for raw in ENV.read_text(encoding="utf-8").splitlines():
            key = raw.split("=", 1)[0].strip()
            if key == "SAP_CREDENTIALS_FILE":
                continue  # 废弃明文文件机制
            if key == "SAP_COMM_PASSWORD":
                lines.append(f'SAP_COMM_PASSWORD="{password}"')
                seen_pw = True
                continue
            lines.append(raw)
    if not seen_pw:
        lines.append(f'SAP_COMM_PASSWORD="{password}"')

    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 删除明文凭证文件
    USER_TXT.unlink()
    print(f"[ok] 已将 SAP 密码迁移至 {ENV.relative_to(ROOT)}（gitignore 已忽略），并删除明文 user.txt")


if __name__ == "__main__":
    main()
