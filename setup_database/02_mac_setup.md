# Mac MySQL 설치 가이드

> **macOS 환경에서 MySQL 8.0 설치 및 설정 (Intel & Apple Silicon 지원)**

## 📋 시스템 요구사항

- **운영체제**: macOS 11.0 (Big Sur) 이상
- **프로세서**: Intel 또는 Apple Silicon (M1/M2/M3)
- **RAM**: 최소 4GB (8GB 권장)
- **디스크**: 최소 2GB 여유 공간
- **관리자 권한**: 설치 과정에서 필요

## 🍺 1단계: Homebrew 설치 확인

### 1.1 Homebrew 설치 확인
```bash
# Homebrew 설치 확인
brew --version
```

### 1.2 Homebrew 설치 (없는 경우)
```bash
# Homebrew 설치
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 설치 후 PATH 설정 (Apple Silicon Mac의 경우)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Intel Mac의 경우
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/usr/local/bin/brew shellenv)"
```

### 1.3 Homebrew 업데이트
```bash
brew update
```

## 🚀 2단계: MySQL 설치

### 2.1 MySQL 검색 및 설치
```bash
# MySQL 패키지 검색
brew search mysql

# MySQL 8.0 설치 (최신 버전)
brew install mysql

# 또는 특정 버전 설치
# brew install mysql@8.0
```

### 2.2 설치 확인
```bash
# 설치된 MySQL 버전 확인
mysql --version

# 설치 위치 확인
brew --prefix mysql
```

**예상 출력:**
```
mysql  Ver 8.0.35 for macos13.3 on arm64 (Homebrew)
/opt/homebrew/Cellar/mysql/8.0.35
```

## ⚙️ 3단계: MySQL 서비스 시작

### 3.1 MySQL 서비스 시작
```bash
# MySQL 서비스 시작
brew services start mysql

# 서비스 상태 확인
brew services list | grep mysql
```

**성공 시 출력:**
```
mysql    started user ~/Library/LaunchAgents/homebrew.mxcl.mysql.plist
```

### 3.2 자동 시작 설정
```bash
# 시스템 부팅 시 자동 시작 설정 (이미 위에서 설정됨)
# brew services start mysql 명령어가 자동으로 설정

# 수동으로 시작/중지하려면:
# brew services stop mysql
# brew services restart mysql
```

## 🔐 4단계: 초기 보안 설정

### 4.1 MySQL 보안 설정 실행
```bash
mysql_secure_installation
```

### 4.2 보안 설정 과정
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

## 🖥️ 5단계: 명령줄 접속 테스트

### 5.1 MySQL 접속
```bash
# Root 사용자로 접속
mysql -u root -p

# 비밀번호 입력 후 mysql> 프롬프트 확인
```

### 5.2 기본 명령어 테스트
```sql
-- MySQL 버전 확인
SELECT VERSION();

-- 현재 사용자 확인
SELECT USER();

-- 데이터베이스 목록 확인
SHOW DATABASES;

-- 문자 인코딩 확인
SHOW VARIABLES LIKE 'character_set%';

-- 나가기
EXIT;
```

## 📊 6단계: GUI 도구 설치 (선택사항)

### 6.1 MySQL Workbench (공식 도구)
```bash
# Homebrew Cask로 설치
brew install --cask mysql-workbench

# 또는 공식 사이트에서 다운로드
# https://dev.mysql.com/downloads/workbench/
```

### 6.2 대안 GUI 도구들
```bash
# Sequel Pro (무료, 인기)
brew install --cask sequel-pro

# TablePlus (유료, 다양한 DB 지원)
brew install --cask tableplus

# phpMyAdmin (웹 기반)
brew install phpmyadmin
```

### 6.3 GUI 도구 연결 설정
```
Host: localhost (또는 127.0.0.1)
Port: 3306
Username: root
Password: [설정한 비밀번호]
```

## 🔧 7단계: 환경 설정

### 7.1 MySQL 명령어 PATH 확인
```bash
# MySQL 명령어 PATH 확인
which mysql

# PATH에 없는 경우 추가 (보통 자동으로 설정됨)
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zprofile
source ~/.zprofile
```

### 7.2 설정 파일 위치 확인
```bash
# MySQL 설정 파일 위치
brew --prefix mysql
ls -la $(brew --prefix mysql)/etc/

# 커스텀 설정이 필요한 경우
# /opt/homebrew/etc/my.cnf 파일 생성 및 편집
```

## 🌐 8단계: 네트워크 설정 (선택사항)

### 8.1 외부 접속 허용 (개발 환경만)
MySQL이 localhost에서만 접속 가능하도록 기본 설정되어 있습니다.

```sql
-- MySQL 접속 후 실행
mysql -u root -p

-- 바인딩 주소 확인
SHOW VARIABLES LIKE 'bind_address';

-- 외부 접속을 허용하려면 설정 파일 수정 필요
-- /opt/homebrew/etc/my.cnf 파일 생성:
```

```ini
[mysqld]
bind-address = 0.0.0.0
```

⚠️ **보안 주의**: 외부 접속은 보안 위험이 있으므로 개발 환경에서만 사용하고 방화벽 설정 필요

### 8.2 방화벽 설정 (필요한 경우)
```bash
# macOS 방화벽 상태 확인
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# 필요한 경우 시스템 환경설정 → 보안 및 개인정보보호 → 방화벽에서 설정
```

## ✅ 9단계: 설치 확인

### 9.1 MySQL 서비스 상태 확인
```bash
# 서비스 상태 확인
brew services list | grep mysql

# 프로세스 확인
ps aux | grep mysql

# 포트 확인
lsof -i :3306
```

### 9.2 연결 테스트
```bash
# 로컬 연결 테스트
mysql -u root -p -h localhost

# TCP/IP 연결 테스트
mysql -u root -p -h 127.0.0.1 -P 3306
```

## 🎯 다음 단계

1. **데이터베이스 초기화**: `./setup_database.sh` 실행
2. **Python 연결 테스트**: `python3 05_python_connection_test.py` 실행
3. **2회차 강의 코드** 실행 준비 완료

## 🔧 주요 경로 및 파일

### Intel Mac (Homebrew):
```
MySQL 설치 경로: /usr/local/Cellar/mysql/8.0.xx/
설정 파일: /usr/local/etc/my.cnf
데이터 디렉토리: /usr/local/var/mysql/
로그 파일: /usr/local/var/mysql/[컴퓨터명].local.err
```

### Apple Silicon Mac (Homebrew):
```
MySQL 설치 경로: /opt/homebrew/Cellar/mysql/8.0.xx/
설정 파일: /opt/homebrew/etc/my.cnf
데이터 디렉토리: /opt/homebrew/var/mysql/
로그 파일: /opt/homebrew/var/mysql/[컴퓨터명].local.err
```

## ⚡ 빠른 문제 해결

| 문제 | 해결 방법 |
|------|-----------|
| **MySQL 서비스 시작 실패** | `brew services restart mysql` 후 로그 확인 |
| **포트 3306 사용 중** | `lsof -i :3306`으로 충돌 프로세스 확인 |
| **비밀번호 분실** | MySQL 안전 모드로 재시작 후 비밀번호 재설정 |
| **Homebrew 권한 문제** | `sudo chown -R $(whoami) $(brew --prefix)/*` |
| **M1 Mac 호환성 문제** | Rosetta 2 설치: `softwareupdate --install-rosetta` |

## 🔄 제거 및 재설치

### 완전 제거 (필요한 경우):
```bash
# MySQL 서비스 중지
brew services stop mysql

# MySQL 제거
brew uninstall mysql

# 데이터 디렉토리 제거 (주의: 모든 데이터 삭제)
rm -rf $(brew --prefix)/var/mysql

# 설정 파일 제거
rm -f $(brew --prefix)/etc/my.cnf

# 재설치
brew install mysql
```

---

**다음**: [데이터베이스 초기화 가이드](./04_database_setup.sql) | [문제 해결](./troubleshooting.md)
