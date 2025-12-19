# Ubuntu MySQL 설치 가이드

> **Ubuntu 20.04/22.04 LTS 환경에서 MySQL 8.0 설치 및 설정**

## 📋 시스템 요구사항

- **운영체제**: Ubuntu 20.04 LTS (Focal) 또는 22.04 LTS (Jammy)
- **아키텍처**: x86_64 (AMD64)
- **RAM**: 최소 2GB (4GB 권장)
- **디스크**: 최소 2GB 여유 공간
- **권한**: sudo 권한 필요

## 🔄 1단계: 시스템 업데이트

### 1.1 패키지 목록 업데이트
```bash
# 패키지 목록 업데이트
sudo apt update

# 시스템 패키지 업그레이드 (선택사항)
sudo apt upgrade -y
```

### 1.2 필수 패키지 설치
```bash
# wget, curl 등 기본 도구 설치
sudo apt install -y wget curl lsb-release gnupg
```

## 🚀 2단계: MySQL 설치

### 2.1 MySQL Server 설치
```bash
# MySQL Server 8.0 설치
sudo apt install -y mysql-server

# 설치 확인
mysql --version
```

**예상 출력:**
```
mysql  Ver 8.0.35-0ubuntu0.22.04.1 for Linux on x86_64 ((Ubuntu))
```

### 2.2 MySQL 서비스 상태 확인
```bash
# MySQL 서비스 상태 확인
sudo systemctl status mysql

# 자동 시작 활성화
sudo systemctl enable mysql

# 서비스 시작 (이미 실행 중일 수 있음)
sudo systemctl start mysql
```

## 🔐 3단계: 초기 보안 설정

### 3.1 MySQL 보안 설정 실행
```bash
sudo mysql_secure_installation
```

### 3.2 보안 설정 과정
다음 질문들에 답변하세요:

```
1. VALIDATE PASSWORD COMPONENT 설치?
   Would you like to setup VALIDATE PASSWORD component? (Press y|Y for Yes, any other key for No): n

2. Root 비밀번호 설정
   New password: [강력한 비밀번호 입력]
   Re-enter new password: [동일한 비밀번호 재입력]

3. 익명 사용자 제거?
   Remove anonymous users? (Press y|Y for Yes, any other key for No): y

4. Root 원격 로그인 비활성화?
   Disallow root login remotely? (Press y|Y for Yes, any other key for No): y

5. test 데이터베이스 제거?
   Remove test database and access to it? (Press y|Y for Yes, any other key for No): y

6. 권한 테이블 다시 로드?
   Reload privilege tables now? (Press y|Y for Yes, any other key for No): y
```

**권장 비밀번호 형식:**
- 최소 8자 이상
- 대문자, 소문자, 숫자, 특수문자 조합
- 예시: `MySQL2024!@#`

## 🔧 4단계: Root 사용자 인증 설정

### 4.1 현재 인증 방식 확인
Ubuntu의 MySQL은 기본적으로 `auth_socket` 플러그인을 사용하므로 비밀번호 인증으로 변경해야 합니다.

```bash
# MySQL Root 접속 (비밀번호 없이)
sudo mysql

# 또는 비밀번호가 설정된 경우
# mysql -u root -p
```

### 4.2 Root 인증 방식 변경
MySQL 프롬프트에서 다음 명령어 실행:

```sql
-- 현재 사용자 인증 방식 확인
SELECT user,authentication_string,plugin,host FROM mysql.user WHERE user='root';

-- Root 사용자 비밀번호 인증으로 변경
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'MySQL2024!@#';

-- 권한 새로고침
FLUSH PRIVILEGES;

-- 변경 확인
SELECT user,authentication_string,plugin,host FROM mysql.user WHERE user='root';

-- MySQL 나가기
EXIT;
```

### 4.3 새로운 인증 방식으로 접속 테스트
```bash
# 비밀번호로 Root 접속
mysql -u root -p

# 비밀번호 입력 후 성공하면 mysql> 프롬프트 표시
```

## 🖥️ 5단계: 기본 설정 확인

### 5.1 MySQL 버전 및 설정 확인
```sql
-- MySQL 버전 확인
SELECT VERSION();

-- 현재 사용자 확인
SELECT USER();

-- 데이터베이스 목록 확인
SHOW DATABASES;

-- 문자 인코딩 확인
SHOW VARIABLES LIKE 'character_set%';

-- 포트 확인
SHOW VARIABLES LIKE 'port';

-- 나가기
EXIT;
```

## 🌐 6단계: 네트워크 설정

### 6.1 바인딩 주소 확인
```bash
# MySQL 설정 파일 확인
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf

# 또는 현재 바인딩 주소 확인
mysql -u root -p -e "SHOW VARIABLES LIKE 'bind_address';"
```

### 6.2 외부 접속 허용 (선택사항)
개발 환경에서 외부 접속이 필요한 경우:

```bash
# MySQL 설정 파일 편집
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf

# 다음 줄을 찾아서:
# bind-address = 127.0.0.1

# 다음과 같이 변경 (모든 IP에서 접속 허용):
# bind-address = 0.0.0.0

# MySQL 서비스 재시작
sudo systemctl restart mysql
```

⚠️ **보안 주의**: 외부 접속은 보안 위험이 있으므로 방화벽 설정과 함께 사용

## 🔥 7단계: 방화벽 설정 (UFW)

### 7.1 UFW 상태 확인
```bash
# UFW 방화벽 상태 확인
sudo ufw status

# UFW가 비활성화된 경우 활성화
sudo ufw enable
```

### 7.2 MySQL 포트 허용 (필요한 경우)
```bash
# 로컬 접속만 허용 (기본값)
# 추가 설정 불필요

# 특정 IP에서 MySQL 접속 허용 예시:
# sudo ufw allow from 192.168.1.0/24 to any port 3306

# 모든 곳에서 MySQL 접속 허용 (권장하지 않음):
# sudo ufw allow 3306
```

## 📊 8단계: GUI 도구 설치 (선택사항)

### 8.1 phpMyAdmin (웹 기반)
```bash
# phpMyAdmin 설치
sudo apt install -y phpmyadmin

# Apache 웹서버도 함께 설치됨
# 브라우저에서 http://localhost/phpmyadmin 접속
```

### 8.2 MySQL Workbench (데스크톱)
```bash
# Snap을 통한 설치
sudo snap install mysql-workbench-community

# 또는 deb 패키지로 설치
# wget https://dev.mysql.com/get/Downloads/MySQLGUITools/mysql-workbench-community_8.0.34-1ubuntu22.04_amd64.deb
# sudo dpkg -i mysql-workbench-community_8.0.34-1ubuntu22.04_amd64.deb
# sudo apt -f install  # 의존성 해결
```

### 8.3 연결 설정
```
Host: localhost (또는 127.0.0.1)
Port: 3306
Username: root
Password: [설정한 비밀번호]
```

## ✅ 9단계: 설치 확인

### 9.1 서비스 상태 확인
```bash
# MySQL 서비스 상태
sudo systemctl status mysql

# MySQL 프로세스 확인
ps aux | grep mysql

# 포트 확인
sudo netstat -tlnp | grep :3306
# 또는
sudo ss -tlnp | grep :3306
```

### 9.2 로그 확인
```bash
# MySQL 오류 로그 확인
sudo tail -f /var/log/mysql/error.log

# 시스템 로그에서 MySQL 관련 확인
sudo journalctl -u mysql.service
```

### 9.3 연결 테스트
```bash
# 로컬 연결 테스트
mysql -u root -p -h localhost

# TCP/IP 연결 테스트
mysql -u root -p -h 127.0.0.1 -P 3306

# 소켓 연결 테스트
mysql -u root -p --socket=/var/run/mysqld/mysqld.sock
```

## 🎯 다음 단계

1. **데이터베이스 초기화**: `chmod +x setup_database.sh && ./setup_database.sh` 실행
2. **Python 연결 테스트**: `python3 05_python_connection_test.py` 실행
3. **2회차 강의 코드** 실행 준비 완료

## 🔧 주요 설정 파일 및 경로

```bash
# MySQL 주 설정 파일
/etc/mysql/mysql.conf.d/mysqld.cnf

# MySQL 데이터 디렉토리
/var/lib/mysql/

# MySQL 로그 파일
/var/log/mysql/error.log

# MySQL 소켓 파일
/var/run/mysqld/mysqld.sock

# MySQL 서비스 파일
/lib/systemd/system/mysql.service
```

## ⚡ 빠른 문제 해결

| 문제 | 해결 방법 |
|------|-----------|
| **MySQL 서비스 시작 실패** | `sudo systemctl restart mysql` 후 `journalctl -u mysql.service` 로그 확인 |
| **포트 3306 사용 중** | `sudo ss -tlnp \| grep :3306`으로 충돌 프로세스 확인 |
| **Root 비밀번호 분실** | MySQL 안전 모드로 재시작 후 비밀번호 재설정 |
| **권한 거부 오류** | `auth_socket` 플러그인 → `mysql_native_password` 변경 확인 |
| **외부 접속 불가** | 방화벽 설정 및 bind-address 확인 |

## 🔄 완전 제거 및 재설치

### 완전 제거 (필요한 경우):
```bash
# MySQL 서비스 중지
sudo systemctl stop mysql

# MySQL 패키지 제거
sudo apt remove --purge mysql-server mysql-client mysql-common

# 설정 파일 및 데이터 제거 (주의: 모든 데이터 삭제)
sudo rm -rf /var/lib/mysql
sudo rm -rf /etc/mysql

# 자동 생성된 사용자 제거
sudo deluser mysql

# 재설치
sudo apt update
sudo apt install -y mysql-server
```

## 📱 원격 접속 사용자 생성 (선택사항)

외부에서 접속할 전용 사용자를 생성하는 경우:

```sql
-- MySQL 접속
mysql -u root -p

-- 원격 접속용 사용자 생성
CREATE USER 'remote_user'@'%' IDENTIFIED BY 'StrongPassword123!';

-- 권한 부여
GRANT ALL PRIVILEGES ON *.* TO 'remote_user'@'%';

-- 권한 새로고침
FLUSH PRIVILEGES;

-- 사용자 확인
SELECT user,host FROM mysql.user WHERE user='remote_user';

EXIT;
```

---

**다음**: [데이터베이스 초기화 가이드](./04_database_setup.sql) | [문제 해결](./troubleshooting.md)
