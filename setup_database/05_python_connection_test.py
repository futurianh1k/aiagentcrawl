#!/usr/bin/env python3
"""
MySQL 연결 테스트 스크립트

이 스크립트는 다음을 확인합니다:
1. 필수 Python 패키지 설치 여부
2. MySQL 서버 연결 가능 여부  
3. 데이터베이스 및 테이블 존재 여부
4. SQLAlchemy ORM 연결 테스트
5. 2회차 강의 코드 실행 준비 상태

작성자: AI Assistant
버전: 1.0
날짜: 2024
"""

import sys
import os
import getpass
from typing import Optional, Dict, List, Tuple
from datetime import datetime

# 색상 출력을 위한 ANSI 코드
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'  # 색상 리셋

def print_colored(text: str, color: str = Colors.WHITE, bold: bool = False) -> None:
    """색상과 스타일을 적용하여 텍스트 출력"""
    style = Colors.BOLD if bold else ''
    print(f"{style}{color}{text}{Colors.ENDC}")

def print_header(title: str) -> None:
    """헤더 스타일로 제목 출력"""
    print()
    print_colored("=" * 80, Colors.CYAN, bold=True)
    print_colored(f" {title}", Colors.CYAN, bold=True)
    print_colored("=" * 80, Colors.CYAN, bold=True)

def print_step(step_num: int, description: str) -> None:
    """단계별 설명 출력"""
    print()
    print_colored(f"[단계 {step_num}] {description}", Colors.BLUE, bold=True)
    print_colored("-" * 60, Colors.BLUE)

def print_success(message: str) -> None:
    """성공 메시지 출력"""
    print_colored(f"✓ {message}", Colors.GREEN)

def print_error(message: str) -> None:
    """오류 메시지 출력"""
    print_colored(f"✗ {message}", Colors.RED)

def print_warning(message: str) -> None:
    """경고 메시지 출력"""
    print_colored(f"⚠ {message}", Colors.YELLOW)

def print_info(message: str) -> None:
    """정보 메시지 출력"""
    print_colored(f"ℹ {message}", Colors.BLUE)

def check_package_installation() -> Dict[str, bool]:
    """필수 Python 패키지 설치 상태 확인"""
    print_step(1, "Python 패키지 설치 상태 확인")

    packages = {
        'mysql.connector': 'mysql-connector-python',
        'sqlalchemy': 'sqlalchemy',
        'pymysql': 'pymysql',
        'pandas': 'pandas',
        'requests': 'requests',
        'bs4': 'beautifulsoup4',
        'selenium': 'selenium',
        'textblob': 'textblob',
        'transformers': 'transformers'
    }

    results = {}

    for import_name, package_name in packages.items():
        try:
            if import_name == 'bs4':
                import bs4
            else:
                __import__(import_name)
            print_success(f"{package_name} 설치됨")
            results[package_name] = True
        except ImportError:
            print_error(f"{package_name} 설치 필요")
            results[package_name] = False

    missing_packages = [pkg for pkg, installed in results.items() if not installed]

    if missing_packages:
        print()
        print_warning("누락된 패키지가 있습니다. 다음 명령어로 설치하세요:")
        print_colored(f"pip install {' '.join(missing_packages)}", Colors.CYAN)
        return results
    else:
        print()
        print_success("모든 필수 패키지가 설치되어 있습니다!")
        return results

def get_connection_info() -> Tuple[str, str, str, str, str]:
    """사용자로부터 데이터베이스 연결 정보 입력받기"""
    print_step(2, "데이터베이스 연결 정보 입력")

    print("MySQL 연결 정보를 입력하세요:")
    print_info("기본값을 사용하려면 Enter를 누르세요")

    host = input(f"Host (기본값: localhost): ").strip() or "localhost"
    port = input(f"Port (기본값: 3306): ").strip() or "3306"
    user = input(f"User (기본값: news_app): ").strip() or "news_app"
    database = input(f"Database (기본값: news_sentiment_analysis): ").strip() or "news_sentiment_analysis"

    # 비밀번호는 보안을 위해 숨김 입력
    print("Password: ", end="")
    password = getpass.getpass("")

    return host, port, user, password, database

def test_mysql_connector(host: str, port: str, user: str, password: str, database: str) -> bool:
    """mysql-connector-python을 사용한 연결 테스트"""
    print_step(3, "MySQL Connector 연결 테스트")

    try:
        import mysql.connector
        print_success("mysql-connector-python 패키지 로드됨")

        # 연결 설정
        config = {
            'host': host,
            'port': int(port),
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'raise_on_warnings': True
        }

        # 연결 시도
        connection = mysql.connector.connect(**config)
        print_success(f"MySQL 서버 연결 성공: {user}@{host}:{port}/{database}")

        # 기본 정보 조회
        cursor = connection.cursor()

        # MySQL 버전 확인
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()
        print_success(f"MySQL 버전: {version[0]}")

        # 문자셋 확인
        cursor.execute("SELECT @@character_set_database, @@collation_database;")
        charset_info = cursor.fetchone()
        print_success(f"문자셋: {charset_info[0]}, 콜레이션: {charset_info[1]}")

        # 테이블 목록 확인
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        print_success(f"데이터베이스 테이블: {len(tables)}개")

        if tables:
            print_info("생성된 테이블:")
            for table_name in table_names:
                print(f"  - {table_name}")

        # 예상 테이블 확인
        expected_tables = {'crawl_sessions', 'articles', 'comments', 'keywords', 'article_keywords'}
        missing_tables = expected_tables - set(table_names)

        if missing_tables:
            print_warning(f"누락된 테이블: {', '.join(missing_tables)}")
            print_info("04_database_setup.sql 스크립트를 실행해주세요")
        else:
            print_success("모든 필수 테이블이 존재합니다!")

        cursor.close()
        connection.close()
        return True

    except ImportError:
        print_error("mysql-connector-python이 설치되지 않았습니다")
        print_info("설치: pip install mysql-connector-python")
        return False
    except Exception as err:
        print_error(f"MySQL 연결 오류: {err}")
        return False

def test_sqlalchemy(host: str, port: str, user: str, password: str, database: str) -> bool:
    """SQLAlchemy를 사용한 연결 테스트"""
    print_step(4, "SQLAlchemy + PyMySQL 연결 테스트")

    try:
        from sqlalchemy import create_engine, text, inspect
        from sqlalchemy.orm import sessionmaker
        print_success("SQLAlchemy 및 PyMySQL 패키지 로드됨")

        # 연결 문자열 생성
        connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"

        # 엔진 생성 (연결 풀 설정)
        engine = create_engine(
            connection_string,
            echo=False,  # SQL 로그 비활성화
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # 연결 상태 확인
            pool_recycle=3600   # 1시간마다 연결 갱신
        )

        # 연결 테스트
        with engine.connect() as conn:
            # 기본 연결 확인
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            if test_value == 1:
                print_success("SQLAlchemy 기본 연결 성공")

            # 데이터베이스 정보 확인
            result = conn.execute(text("SELECT DATABASE(), USER(), VERSION()"))
            db_info = result.fetchone()
            print_success(f"현재 DB: {db_info[0]}, 사용자: {db_info[1]}")
            print_info(f"MySQL 버전: {db_info[2]}")

            # 테이블 메타데이터 확인 (Inspector 사용)
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            print_success(f"SQLAlchemy를 통한 테이블 조회: {len(table_names)}개")

            # 각 테이블의 레코드 수 확인
            table_stats = {}
            for table_name in table_names:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
                    row_count = result.fetchone()[0]
                    table_stats[table_name] = row_count
                except Exception as e:
                    table_stats[table_name] = f"오류: {str(e)[:50]}..."

            if table_stats:
                print_info("테이블별 레코드 수:")
                for table, count in table_stats.items():
                    print(f"  - {table}: {count}")

        # Session 테스트 (ORM)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # 간단한 쿼리 실행
            result = session.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = :schema"), 
                                   {"schema": database})
            table_count = result.fetchone()[0]
            print_success(f"ORM 세션을 통한 테이블 확인: {table_count}개")

        finally:
            session.close()

        print_success("SQLAlchemy 모든 테스트 통과!")
        return True

    except ImportError as e:
        print_error(f"필수 패키지 누락: {e}")
        print_info("설치: pip install sqlalchemy pymysql")
        return False
    except Exception as e:
        print_error(f"SQLAlchemy 연결 실패: {e}")
        return False

def test_lecture_readiness(host: str, port: str, user: str, password: str, database: str) -> bool:
    """2회차 강의 코드 실행 준비 상태 확인"""
    print_step(5, "2회차 강의 준비상태 확인")

    try:
        from sqlalchemy import create_engine, text

        connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
        engine = create_engine(connection_string, echo=False)

        readiness_checks = []

        with engine.connect() as conn:
            # 1. 필수 테이블 존재 확인
            expected_tables = ['crawl_sessions', 'articles', 'comments', 'keywords', 'article_keywords']

            for table in expected_tables:
                result = conn.execute(text(f'''
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = '{database}' AND table_name = '{table}'
                '''))
                exists = result.fetchone()[0] > 0

                if exists:
                    print_success(f"테이블 '{table}' 존재 확인")
                    readiness_checks.append(True)
                else:
                    print_error(f"테이블 '{table}' 누락")
                    readiness_checks.append(False)

            # 2. 뷰 존재 확인
            expected_views = ['v_article_stats', 'v_keyword_popularity', 'v_daily_sentiment_trend']

            for view in expected_views:
                result = conn.execute(text(f'''
                    SELECT COUNT(*) FROM information_schema.views 
                    WHERE table_schema = '{database}' AND table_name = '{view}'
                '''))
                exists = result.fetchone()[0] > 0

                if exists:
                    print_success(f"뷰 '{view}' 존재 확인")
                    readiness_checks.append(True)
                else:
                    print_warning(f"뷰 '{view}' 누락 (선택사항)")

            # 3. 기본 키워드 데이터 확인
            result = conn.execute(text("SELECT COUNT(*) FROM keywords WHERE is_active = 1"))
            keyword_count = result.fetchone()[0]

            if keyword_count > 0:
                print_success(f"활성 키워드: {keyword_count}개")
                readiness_checks.append(True)
            else:
                print_warning("기본 키워드가 없습니다 (선택사항)")

            # 4. UTF8MB4 인코딩 확인
            result = conn.execute(text("SELECT @@character_set_database"))
            charset = result.fetchone()[0]

            if charset.lower() in ['utf8mb4']:
                print_success(f"문자셋 확인: {charset} (다국어 지원)")
                readiness_checks.append(True)
            else:
                print_warning(f"문자셋: {charset} (UTF8MB4 권장)")
                readiness_checks.append(False)

        # 5. Python 패키지 최종 확인
        required_packages = ['requests', 'beautifulsoup4', 'selenium', 'textblob', 'transformers']
        package_ok = True

        for pkg in required_packages:
            try:
                if pkg == 'beautifulsoup4':
                    import bs4
                else:
                    __import__(pkg)
            except ImportError:
                print_error(f"패키지 '{pkg}' 누락")
                package_ok = False

        if package_ok:
            print_success("2회차 강의 필수 패키지 모두 설치됨")
            readiness_checks.append(True)
        else:
            readiness_checks.append(False)

        # 전체 결과 판정
        passed_checks = sum(readiness_checks)
        total_checks = len(readiness_checks)

        print()
        print_colored(f"준비도 검사 결과: {passed_checks}/{total_checks} 통과", Colors.CYAN, bold=True)

        if passed_checks >= total_checks - 1:  # 최소 1개까지는 실패해도 OK
            return True
        else:
            return False

    except Exception as e:
        print_error(f"준비상태 확인 실패: {e}")
        return False

def create_connection_template(host: str, port: str, user: str, password: str, database: str) -> None:
    """연결 설정 템플릿 생성"""
    print_step(6, "연결 설정 템플릿 생성")

    # 보안을 위해 비밀번호는 플레이스홀더로 대체
    safe_password = "your_password_here"

    template_content = f'''# MySQL 연결 설정 템플릿
# 생성일: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# 1. mysql-connector-python 사용
import mysql.connector

mysql_config = {{
    'host': '{host}',
    'port': {port},
    'user': '{user}',
    'password': '{safe_password}',
    'database': '{database}',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'raise_on_warnings': True
}}

# 연결 예시
connection = mysql.connector.connect(**mysql_config)

# 2. SQLAlchemy 사용 (2회차 강의 코드)
from sqlalchemy import create_engine

DATABASE_URL = "mysql+pymysql://{user}:{safe_password}@{host}:{port}/{database}?charset=utf8mb4"
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# 3. 환경변수 설정 (권장)
import os

# .env 파일에 저장하거나 환경변수로 설정
os.environ['MYSQL_HOST'] = '{host}'
os.environ['MYSQL_PORT'] = '{port}'
os.environ['MYSQL_USER'] = '{user}'
os.environ['MYSQL_PASSWORD'] = '{safe_password}'
os.environ['MYSQL_DATABASE'] = '{database}'

# 환경변수에서 읽어오기
DATABASE_URL = f"mysql+pymysql://{{os.getenv('MYSQL_USER')}}:{{os.getenv('MYSQL_PASSWORD')}}@{{os.getenv('MYSQL_HOST')}}:{{os.getenv('MYSQL_PORT')}}/{{os.getenv('MYSQL_DATABASE')}}?charset=utf8mb4"
'''

    try:
        with open('mysql_connection_template.py', 'w', encoding='utf-8') as f:
            f.write(template_content)
        print_success("연결 설정 템플릿 파일 생성: mysql_connection_template.py")
    except Exception as e:
        print_warning(f"템플릿 파일 생성 실패: {e}")
        print_info("아래 내용을 복사하여 사용하세요:")
        print_colored(template_content, Colors.CYAN)

def main():
    """메인 함수"""
    print_header("MySQL 연결 테스트 스크립트")
    print_colored("2회차 강의: AI 에이전트 기반 뉴스 감정분석 시스템", Colors.MAGENTA, bold=True)
    print_colored("MySQL 설치 및 Python 연결 상태를 확인합니다", Colors.WHITE)

    # 1. 패키지 설치 상태 확인
    package_results = check_package_installation()

    # 필수 패키지 누락 시 경고
    if not all([package_results.get('mysql-connector-python', False), 
                package_results.get('sqlalchemy', False),
                package_results.get('pymysql', False)]):
        print()
        print_warning("MySQL 연결에 필요한 패키지가 누락되었습니다")
        print_info("패키지를 설치한 후 다시 실행해주세요")
        return 1

    # 2. 연결 정보 입력
    try:
        host, port, user, password, database = get_connection_info()
    except KeyboardInterrupt:
        print()
        print_info("사용자가 취소했습니다")
        return 0

    # 3. 연결 테스트 실행
    print_header("연결 테스트 시작")

    test_results = []

    # MySQL Connector 테스트
    mysql_test = test_mysql_connector(host, port, user, password, database)
    test_results.append(("MySQL Connector", mysql_test))

    # SQLAlchemy 테스트
    if mysql_test:  # 기본 연결이 성공한 경우에만
        sqlalchemy_test = test_sqlalchemy(host, port, user, password, database)
        test_results.append(("SQLAlchemy", sqlalchemy_test))

        # 강의 준비상태 확인
        if sqlalchemy_test:
            readiness_test = test_lecture_readiness(host, port, user, password, database)
            test_results.append(("강의 준비상태", readiness_test))

            # 연결 템플릿 생성
            create_connection_template(host, port, user, password, database)

    # 4. 최종 결과 출력
    print_header("테스트 결과 요약")

    all_passed = True
    for test_name, result in test_results:
        if result:
            print_success(f"{test_name}: 통과")
        else:
            print_error(f"{test_name}: 실패")
            all_passed = False

    print()
    if all_passed and len(test_results) >= 3:
        print_colored("🎉 모든 테스트를 통과했습니다!", Colors.GREEN, bold=True)
        print_colored("2회차 강의 코드를 실행할 준비가 완료되었습니다.", Colors.GREEN)
        print()
        print_info("다음 단계:")
        print("  1. 2회차 강의 자료를 다운로드하세요")
        print("  2. mysql_connection_template.py 파일의 비밀번호를 실제 값으로 변경하세요")
        print("  3. 뉴스 크롤링 및 감정분석 코드를 실행하세요")
        return 0
    else:
        print_colored("⚠️ 일부 테스트가 실패했습니다.", Colors.YELLOW, bold=True)
        print()
        print_info("문제 해결 방법:")
        print("  1. troubleshooting.md 파일을 확인하세요")
        print("  2. MySQL 서비스가 실행 중인지 확인하세요")
        print("  3. 데이터베이스와 사용자가 올바르게 생성되었는지 확인하세요")
        print("  4. 04_database_setup.sql 스크립트를 다시 실행해보세요")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print()
        print_info("프로그램이 사용자에 의해 중단되었습니다")
        sys.exit(0)
    except Exception as e:
        print()
        print_error(f"예상치 못한 오류가 발생했습니다: {e}")
        sys.exit(1)
