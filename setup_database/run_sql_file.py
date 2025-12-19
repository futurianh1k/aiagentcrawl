#!/usr/bin/env python3
"""
MySQL에 .sql 파일을 안전하게 실행하기 위한 유틸리티 스크립트 (한국어 설명)

기능 요약:
- 로컬 또는 지정된 경로의 .sql 파일을 읽어 MySQL 서버에 순차적으로 실행합니다.
- 환경변수(MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)
  또는 CLI 인자로 접속 정보를 전달할 수 있습니다.
- SELECT 쿼리의 결과를 옵션으로 출력할 수 있습니다.
- 기본적으로 실행 전에 확인을 요구하며, --no-commit 옵션으로 롤백(커밋 안함) 테스트를 지원합니다.

주의 및 동작 상세:
- DDL(데이터베이스/테이블 생성 등)은 MySQL에서 자동 커밋될 수 있으므로
  --no-commit 옵션이 항상 DDL을 되돌리지 못할 수 있음을 명심하세요.
- 서버 연결 실패, 권한 문제, SQL 에러 등은 적절한 종료 코드를 반환합니다.

종료 코드(대략적):
- 0 : 성공
- 1 : 잘못된 입력(파일 없음 등)
- 2 : mysql-connector-python 미설치
- 3 : 연결 실패 (인증/네트워크)
- 4 : SQL 실행 중 오류

사용 예시:
  python run_sql_file.py --file 04_database_setup.sql
  MYSQL_HOST=localhost MYSQL_USER=root MYSQL_PASSWORD=secret python run_sql_file.py --auto-yes --show-results
  # 커밋하지 않고 테스트만 할 때
  python run_sql_file.py --file setup.sql --no-commit --auto-yes

보안 권장사항:
- 비밀번호를 CLI 인자로 직접 전달하지 말고 환경변수나 안전한 시크릿 매니저를 사용하세요.
- 프로덕션 DB에 실행하기 전에는 항상 백업을 권장합니다.

요구 패키지:
  pip install mysql-connector-python

Author: GitHub Copilot
"""

from __future__ import annotations
import argparse
import os
import sys
import getpass
from typing import Optional

try:
    import mysql.connector
    from mysql.connector import Error
except Exception:
    mysql = None
    Error = Exception


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute an SQL file against a MySQL server")
    parser.add_argument("--file", "-f", default=os.path.join(os.path.dirname(__file__), "04_database_setup.sql"),
                        help="Path to the .sql file to execute (default: 04_database_setup.sql)")
    parser.add_argument("--host", default=os.getenv("MYSQL_HOST", "localhost"), help="MySQL host")
    parser.add_argument("--port", default=os.getenv("MYSQL_PORT", "3306"), help="MySQL port")
    parser.add_argument("--user", default=os.getenv("MYSQL_USER", "root"), help="MySQL user")
    parser.add_argument("--password", default=os.getenv("MYSQL_PASSWORD"), help="MySQL password")
    parser.add_argument("--database", default=os.getenv("MYSQL_DATABASE"), help="Default database (optional)")
    parser.add_argument("--commit", dest="commit", action="store_true", default=True, help="Commit changes (default: True)")
    parser.add_argument("--no-commit", dest="commit", action="store_false", help="Do not commit (run in transaction and roll back at the end)")
    parser.add_argument("--auto-yes", dest="auto_yes", action="store_true", help="Do not prompt before executing")
    parser.add_argument("--show-results", dest="show_results", action="store_true", help="Print SELECT results")
    parser.add_argument("--encoding", default="utf-8", help="File encoding (default: utf-8)")
    return parser.parse_args()


def read_sql_file(path: str, encoding: str = "utf-8") -> str:
    with open(path, "r", encoding=encoding) as f:
        return f.read()


def ask_password_if_missing(password: Optional[str], user: str) -> str:
    if password:
        return password
    try:
        return getpass.getpass(f"Password for {user}: ")
    except Exception:
        return ""


def execute_sql_script(sql_text: str, host: str, port: int, user: str, password: str, database: Optional[str], commit: bool, show_results: bool) -> int:
    if mysql is None:
        print("Error: mysql-connector-python is not installed. Install with: pip install mysql-connector-python")
        return 2

    # Connect without specifying database to allow CREATE DATABASE statements
    connect_kwargs = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "charset": "utf8mb4",
        "use_unicode": True,
        "raise_on_warnings": True,
    }

    # Only include database if explicitly provided (optional)
    if database:
        connect_kwargs["database"] = database

    try:
        conn = mysql.connector.connect(**connect_kwargs)
    except Error as e:
        print(f"Connection error: {e}")
        return 3

    try:
        cursor = conn.cursor()

        print("Starting execution of SQL script. This may take a while for large scripts...")

        # Execute multiple statements
        for result in cursor.execute(sql_text, multi=True):
            stmt = (result.statement or "").strip()
            if not stmt:
                continue
            # Print a short preview of the statement
            preview = stmt.replace("\n", " ")[:200]
            print(f"-- Executing: {preview}{'...' if len(preview) == 200 else ''}")

            try:
                if result.with_rows:
                    rows = result.fetchall()
                    if show_results:
                        # Print up to first 10 rows
                        for r in rows[:10]:
                            print(r)
                        if len(rows) > 10:
                            print(f"... and {len(rows)-10} more rows")
                    print(f"  -> Returned {len(rows)} rows")
                else:
                    print(f"  -> Affected rows: {result.rowcount}")
            except Error as e:
                # Some statements (e.g., CREATE DATABASE) may not produce row info
                print(f"  -> Statement executed (no result to fetch): {e}")

        # Commit or rollback according to flag
        if commit:
            conn.commit()
            print("All statements executed and committed.")
        else:
            conn.rollback()
            print("Execution finished, rolled back (no commit).")

    except Error as e:
        # On error, rollback to avoid partial changes
        try:
            conn.rollback()
        except Exception:
            pass
        print(f"Error while executing SQL: {e}")
        return 4

    finally:
        cursor.close()
        conn.close()

    return 0


def main() -> int:
    args = parse_args()

    if not os.path.isfile(args.file):
        print(f"SQL file not found: {args.file}")
        return 1

    sql_text = read_sql_file(args.file, encoding=args.encoding)

    host = args.host
    port = int(args.port)
    user = args.user
    password = ask_password_if_missing(args.password, user)
    database = args.database

    print("SQL file:", args.file)
    print(f"MySQL host={host} port={port} user={user} database={(database or '<none>')}")

    if not args.auto_yes:
        resp = input("Proceed to execute the SQL script? [y/N]: ").strip().lower()
        if resp not in ("y", "yes"):
            print("Cancelled by user.")
            return 0

    print("Running script...")
    exit_code = execute_sql_script(sql_text, host, port, user, password, database, args.commit, args.show_results)
    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)
