# MySQL 설치 및 연결 문제 해결 가이드

> **2회차 강의: AI 에이전트 기반 뉴스 감정분석 시스템** 트러블슈팅 매뉴얼

## 📋 목차

1. [일반적인 문제](#일반적인-문제)
2. [Windows 관련 문제](#windows-관련-문제)  
3. [Mac 관련 문제](#mac-관련-문제)
4. [Ubuntu/Linux 관련 문제](#ubuntulinux-관련-문제)
5. [Python 연결 문제](#python-연결-문제)
6. [데이터베이스 관련 문제](#데이터베이스-관련-문제)
7. [네트워크 및 방화벽 문제](#네트워크-및-방화벽-문제)
8. [성능 최적화](#성능-최적화)
9. [고급 문제 해결](#고급-문제-해결)

---

## 일반적인 문제

### ❌ "MySQL 서버에 연결할 수 없음" (Connection refused)

**증상:**
```
ERROR 2003 (HY000): Can't connect to MySQL server on 'localhost' (10061)
```

**원인 및 해결:**

1. **MySQL 서비스가 실행되지 않음**
   ```bash
   # 서비스 상태 확인
   # Windows:
   sc query MySQL80

   # Mac:
   brew services list | grep mysql

   # Ubuntu:
   sudo systemctl status mysql

   # 서비스 시작
   # Windows:
   net start MySQL80

   # Mac:
   brew services start mysql

   # Ubuntu:
   sudo systemctl start mysql
   ```

2. **포트 충돌 확인**
   ```bash
   # 포트 3306 사용 현황 확인
   # Windows:
   netstat -an | findstr :3306

   # Mac/Linux:
   lsof -i :3306
   sudo ss -tlnp | grep :3306
   ```

3. **방화벽 차단**
   - Windows: Windows Defender 방화벽에서 MySQL 허용
   - Mac: 시스템 환경설정 → 보안 및 개인정보보호 → 방화벽
   - Ubuntu: `sudo ufw allow 3306`

### ❌ "Access denied" (인증 실패)

**증상:**
```
ERROR 1045 (28000): Access denied for user 'root'@'localhost' (using password: YES)
```

**해결 방법:**

1. **비밀번호 확인**
   - 설치 시 설정한 비밀번호 재확인
   - 대소문자 구분 주의

2. **Root 비밀번호 재설정**
   ```bash
   # MySQL 안전 모드 시작
   # Windows:
   mysqld --skip-grant-tables --skip-networking

   # Mac/Linux:
   sudo mysqld_safe --skip-grant-tables --skip-networking &

   # 비밀번호 없이 접속
   mysql -u root

   # 비밀번호 변경
   USE mysql;
   UPDATE user SET authentication_string=PASSWORD('new_password') WHERE User='root';
   FLUSH PRIVILEGES;
   EXIT;

   # MySQL 재시작
   ```

3. **Ubuntu의 auth_socket 문제**
   ```sql
   -- MySQL 접속 (sudo mysql)
   sudo mysql

   -- Root 사용자 인증 방식 변경
   ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_password';
   FLUSH PRIVILEGES;
   EXIT;
   ```

### ❌ "데이터베이스가 존재하지 않음"

**증상:**
```
ERROR 1049 (42000): Unknown database 'news_sentiment_analysis'
```

**해결:**
```bash
# 04_database_setup.sql 스크립트 재실행
mysql -u root -p < 04_database_setup.sql

# 또는 수동 생성
mysql -u root -p
CREATE DATABASE news_sentiment_analysis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## Windows 관련 문제

### ❌ MySQL Installer 문제

**문제 1: "이 앱이 PC에서 실행될 수 없습니다"**
- **해결:** 관리자 권한으로 실행
- **방법:** 파일 우클릭 → "관리자 권한으로 실행"

**문제 2: Visual C++ Redistributable 오류**
- **해결:** Microsoft Visual C++ 재배포 패키지 설치
- **다운로드:** [Microsoft 공식 사이트](https://docs.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)

**문제 3: 서비스 설치 실패**
```cmd
# 수동 서비스 등록
sc create MySQL80 binPath= "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe --defaults-file=C:\ProgramData\MySQL\MySQL Server 8.0\my.ini MySQL80"

# 서비스 시작
sc start MySQL80
```

### ❌ 환경 변수 PATH 문제

**증상:** `'mysql' is not recognized as an internal or external command`

**해결:**
1. **시작 메뉴** → **시스템 환경 변수 편집**
2. **환경 변수** 클릭
3. **시스템 변수**에서 **Path** 선택 후 **편집**
4. **새로 만들기**로 경로 추가:
   ```
   C:\Program Files\MySQL\MySQL Server 8.0\bin
   ```
5. 새 명령 프롬프트 열어서 테스트

### ❌ 포트 충돌 (Windows)

**확인:**
```cmd
netstat -ano | findstr :3306
```

**해결:**
```cmd
# 프로세스 강제 종료
taskkill /PID [PID번호] /F

# MySQL 포트 변경 (my.ini 파일)
# 위치: C:\ProgramData\MySQL\MySQL Server 8.0\my.ini
[mysqld]
port=3307
```

---

## Mac 관련 문제

### ❌ Homebrew 문제

**문제 1: Homebrew 설치되지 않음**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# PATH 설정 (Apple Silicon)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

**문제 2: brew 권한 오류**
```bash
sudo chown -R $(whoami) $(brew --prefix)/*
```

**문제 3: MySQL 설치 실패**
```bash
# Homebrew 업데이트
brew update
brew upgrade

# 캐시 정리
brew cleanup

# MySQL 재설치
brew uninstall mysql
brew install mysql
```

### ❌ M1/M2 Mac 호환성 문제

**Rosetta 2 설치:**
```bash
softwareupdate --install-rosetta
```

**아키텍처 확인:**
```bash
# 현재 아키텍처 확인
uname -m

# MySQL 프로세스 아키텍처 확인
file $(which mysql)
```

### ❌ MySQL 서비스 시작 실패

**해결:**
```bash
# 소유권 수정
sudo chown -R _mysql:_mysql /opt/homebrew/var/mysql

# 권한 수정
chmod 755 /opt/homebrew/var/mysql

# 서비스 재시작
brew services restart mysql

# 로그 확인
tail -f /opt/homebrew/var/mysql/*.err
```

---

## Ubuntu/Linux 관련 문제

### ❌ 패키지 설치 실패

**APT 저장소 문제:**
```bash
# 패키지 목록 업데이트
sudo apt update

# 손상된 패키지 복구
sudo apt --fix-broken install

# MySQL 재설치
sudo apt remove --purge mysql-server mysql-client mysql-common
sudo apt autoremove
sudo apt autoclean
sudo apt install mysql-server
```

### ❌ systemd 서비스 문제

**서비스 상태 확인:**
```bash
# 서비스 상태
sudo systemctl status mysql

# 로그 확인
sudo journalctl -u mysql.service -f

# 서비스 재시작
sudo systemctl restart mysql

# 부팅 시 자동 시작 설정
sudo systemctl enable mysql
```

### ❌ 소켓 파일 문제

**증상:** `Can't connect to local MySQL server through socket`

**해결:**
```bash
# 소켓 파일 위치 확인
mysql --help | grep socket

# 소켓 파일 생성 (없는 경우)
sudo mkdir -p /var/run/mysqld
sudo chown mysql:mysql /var/run/mysqld

# MySQL 재시작
sudo systemctl restart mysql
```

### ❌ AppArmor 보안 문제

**해결:**
```bash
# AppArmor 상태 확인
sudo aa-status | grep mysql

# MySQL AppArmor 프로필 비활성화 (임시)
sudo aa-disable /usr/sbin/mysqld

# 영구적 해결 (설정 파일 수정)
sudo nano /etc/apparmor.d/usr.sbin.mysqld
```

---

## Python 연결 문제

### ❌ 패키지 import 오류

**mysql.connector 문제:**
```bash
# 패키지 재설치
pip uninstall mysql-connector-python
pip install mysql-connector-python

# 대안 설치
pip install mysql-connector-python-rf
```

**SQLAlchemy 문제:**
```bash
# PyMySQL 설치 확인
pip install sqlalchemy pymysql

# 연결 문자열 확인
mysql+pymysql://user:password@host:port/database?charset=utf8mb4
```

### ❌ SSL 연결 오류

**증상:** `SSL connection error`

**해결:**
```python
# mysql.connector에서 SSL 비활성화
import mysql.connector

config = {
    'host': 'localhost',
    'user': 'news_app',
    'password': 'your_password',
    'database': 'news_sentiment_analysis',
    'ssl_disabled': True
}

connection = mysql.connector.connect(**config)
```

```python
# SQLAlchemy에서 SSL 비활성화
from sqlalchemy import create_engine

DATABASE_URL = "mysql+pymysql://user:password@host:port/database?ssl_ca="
engine = create_engine(DATABASE_URL, connect_args={"ssl": {"ssl_disabled": True}})
```

### ❌ 문자 인코딩 문제

**해결:**
```python
# 연결 설정에서 UTF8MB4 명시
config = {
    'host': 'localhost',
    'user': 'news_app', 
    'password': 'your_password',
    'database': 'news_sentiment_analysis',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'use_unicode': True
}
```

---

## 데이터베이스 관련 문제

### ❌ 테이블 생성 실패

**권한 문제:**
```sql
-- 사용자 권한 확인
SHOW GRANTS FOR 'news_app'@'localhost';

-- 권한 부여
GRANT ALL PRIVILEGES ON news_sentiment_analysis.* TO 'news_app'@'localhost';
FLUSH PRIVILEGES;
```

**스토리지 엔진 문제:**
```sql
-- InnoDB 활성화 확인
SHOW ENGINES;

-- 기본 스토리지 엔진 설정
SET default_storage_engine=InnoDB;
```

### ❌ 문자셋 문제

**확인:**
```sql
-- 데이터베이스 문자셋 확인
SHOW CREATE DATABASE news_sentiment_analysis;

-- 변수 확인
SHOW VARIABLES LIKE 'character_set%';
SHOW VARIABLES LIKE 'collation%';
```

**수정:**
```sql
-- 데이터베이스 문자셋 변경
ALTER DATABASE news_sentiment_analysis 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 테이블 문자셋 변경
ALTER TABLE articles 
CONVERT TO CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

### ❌ 외래키 제약조건 오류

**해결:**
```sql
-- 외래키 체크 임시 비활성화
SET FOREIGN_KEY_CHECKS=0;

-- 테이블 생성 또는 수정 작업 수행

-- 외래키 체크 재활성화
SET FOREIGN_KEY_CHECKS=1;
```

---

## 네트워크 및 방화벽 문제

### ❌ 원격 접속 불가

**MySQL 바인드 주소 확인:**
```sql
SHOW VARIABLES LIKE 'bind_address';
```

**설정 변경:**
```ini
# my.cnf 또는 my.ini 파일
[mysqld]
bind-address = 0.0.0.0
```

**사용자 호스트 권한:**
```sql
-- 원격 접속 허용 사용자 생성
CREATE USER 'news_app'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON news_sentiment_analysis.* TO 'news_app'@'%';
FLUSH PRIVILEGES;
```

### ❌ 방화벽 설정

**Windows:**
```cmd
# 방화벽 규칙 추가
netsh advfirewall firewall add rule name="MySQL" dir=in action=allow protocol=TCP localport=3306
```

**Mac:**
```bash
# 방화벽 상태 확인
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

**Ubuntu:**
```bash
# UFW 방화벽 설정
sudo ufw allow 3306
sudo ufw reload
```

---

## 성능 최적화

### ⚡ 느린 쿼리 최적화

**슬로우 쿼리 로그 활성화:**
```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;
SHOW VARIABLES LIKE 'slow_query_log%';
```

**인덱스 확인 및 최적화:**
```sql
-- 테이블 인덱스 확인
SHOW INDEX FROM articles;

-- 쿼리 실행 계획 확인
EXPLAIN SELECT * FROM articles WHERE source = 'naver';

-- 인덱스 추가
CREATE INDEX idx_source_published ON articles(source, published_at);
```

### ⚡ 메모리 설정 최적화

**주요 설정 (my.cnf/my.ini):**
```ini
[mysqld]
# 기본 메모리 설정 (8GB RAM 기준)
innodb_buffer_pool_size = 2G
key_buffer_size = 256M
query_cache_size = 128M
tmp_table_size = 64M
max_heap_table_size = 64M

# 연결 설정
max_connections = 200
connect_timeout = 10
wait_timeout = 600

# InnoDB 설정
innodb_file_per_table = 1
innodb_flush_log_at_trx_commit = 2
innodb_log_file_size = 256M
```

---

## 고급 문제 해결

### 🔧 MySQL 로그 분석

**오류 로그 위치:**
```bash
# Windows
C:\ProgramData\MySQL\MySQL Server 8.0\Data\[컴퓨터명].err

# Mac (Homebrew)
/opt/homebrew/var/mysql/[컴퓨터명].local.err

# Ubuntu
/var/log/mysql/error.log
```

**로그 실시간 모니터링:**
```bash
# Linux/Mac
tail -f /var/log/mysql/error.log

# Windows (PowerShell)
Get-Content "C:\ProgramData\MySQL\MySQL Server 8.0\Data\컴퓨터명.err" -Wait -Tail 10
```

### 🔧 데이터베이스 복구

**테이블 검사 및 복구:**
```sql
-- 테이블 체크
CHECK TABLE articles;

-- 테이블 복구
REPAIR TABLE articles;

-- 테이블 최적화
OPTIMIZE TABLE articles;
```

**전체 데이터베이스 백업:**
```bash
# 백업
mysqldump -u root -p news_sentiment_analysis > backup.sql

# 복원
mysql -u root -p news_sentiment_analysis < backup.sql
```

### 🔧 완전 재설치 가이드

**Windows:**
```cmd
# MySQL 서비스 중지
net stop MySQL80

# 프로그램 제거 (제어판)
# 데이터 폴더 삭제
rmdir /s "C:\ProgramData\MySQL"

# MySQL Installer로 재설치
```

**Mac:**
```bash
# MySQL 완전 제거
brew services stop mysql
brew uninstall mysql
rm -rf /opt/homebrew/var/mysql
rm -rf /opt/homebrew/etc/my.cnf

# 재설치
brew install mysql
```

**Ubuntu:**
```bash
# 완전 제거
sudo systemctl stop mysql
sudo apt remove --purge mysql-server mysql-client mysql-common
sudo rm -rf /var/lib/mysql
sudo rm -rf /etc/mysql

# 재설치
sudo apt update
sudo apt install mysql-server
```

---

## 🆘 추가 도움 요청

### 커뮤니티 지원

- **MySQL 공식 포럼:** [MySQL Community Forum](https://forums.mysql.com/)
- **Stack Overflow:** [MySQL 태그](https://stackoverflow.com/questions/tagged/mysql)
- **MySQL 공식 문서:** [MySQL Documentation](https://dev.mysql.com/doc/)

### 로그 수집 방법

문제 해결을 위해 다음 정보를 수집하세요:

1. **시스템 정보:**
   ```bash
   # 운영체제 및 버전
   uname -a  # Linux/Mac
   systeminfo | findstr "OS"  # Windows
   ```

2. **MySQL 버전:**
   ```sql
   SELECT VERSION();
   ```

3. **오류 메시지:**
   - 정확한 오류 메시지 전문
   - 발생 시점 및 상황

4. **설정 파일:**
   - my.cnf 또는 my.ini 파일 내용
   - 연결 설정 코드

### 긴급 연락처

**강의 관련 문의:**
- 강의 Q&A 게시판 우선 이용
- 이메일 문의 시 상세한 오류 로그 첨부

---

**🔄 마지막 업데이트:** 2024년 12월  
**📝 작성자:** AI Assistant  
**📖 버전:** 1.0
