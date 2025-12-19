# Windows MySQL 설치 가이드

> **Windows 10/11 환경에서 MySQL 8.0 설치 및 설정**

## 📋 시스템 요구사항

- **운영체제**: Windows 10 (64-bit) 또는 Windows 11
- **RAM**: 최소 4GB (8GB 권장)
- **디스크**: 최소 2GB 여유 공간
- **관리자 권한**: 설치 과정에서 필요

## 🔽 1단계: MySQL Installer 다운로드

### 1.1 공식 사이트 접속
1. 웹 브라우저에서 [MySQL 공식 다운로드 페이지](https://dev.mysql.com/downloads/installer/) 접속
2. **MySQL Installer for Windows** 섹션에서 다음 중 하나 선택:
   - `mysql-installer-web-community-8.0.xx.x.msi` (온라인 설치, 약 2MB)
   - `mysql-installer-community-8.0.xx.x.msi` (오프라인 설치, 약 400MB) ⭐ **권장**

### 1.2 다운로드
- "Download" 버튼 클릭
- Oracle 계정 생성 요구 시 "No thanks, just start my download" 클릭하여 건너뛰기

## 🚀 2단계: MySQL 설치

### 2.1 Installer 실행
1. 다운로드한 `.msi` 파일을 **관리자 권한으로 실행**
2. Windows에서 보안 경고 시 "실행" 클릭

### 2.2 설치 타입 선택
**Developer Default** 선택 ⭐ **강력 권장**
- MySQL Server, MySQL Workbench, Connectors, Documentation 포함
- 개발에 필요한 모든 구성 요소 자동 설치

```
설치 타입 옵션:
├── Developer Default    ⭐ 권장 (개발환경 완전 구성)
├── Server only         (서버만 설치)
├── Client only         (클라이언트 도구만)
├── Full               (모든 제품 설치, 용량 큼)
└── Custom             (수동 선택)
```

### 2.3 요구사항 확인
- "Check Requirements" 단계에서 누락된 구성 요소 확인
- **Microsoft Visual C++ Redistributable** 등 필요 시 자동 설치
- "Next" 클릭하여 계속

### 2.4 설치 진행
- "Execute" 클릭하여 설치 시작
- ☕ 설치 완료까지 5-10분 대기 (인터넷 속도에 따라 차이)

## ⚙️ 3단계: MySQL Server 구성

### 3.1 High Availability (고가용성)
- **Standalone MySQL Server** 선택 ⭐ **권장**
- "Next" 클릭

### 3.2 Type and Networking (네트워크 설정)
```
Config Type: Development Computer ⭐ 권장
TCP/IP: ✅ 체크 (활성화)
Port: 3306 (기본값 유지)
X Protocol Port: 33060 (기본값 유지)
```
- "Next" 클릭

### 3.3 Authentication Method (인증 방식)
- **Use Strong Password Encryption (RECOMMENDED)** 선택 ⭐
- MySQL 8.0의 개선된 보안 기능 사용
- "Next" 클릭

### 3.4 Accounts and Roles (계정 설정)
#### Root 비밀번호 설정 🔑 **중요**
```
MySQL Root Password: [강력한 비밀번호 입력]
Repeat Password: [동일한 비밀번호 재입력]
```

**비밀번호 요구사항:**
- 최소 8자 이상
- 대문자, 소문자, 숫자, 특수문자 조합
- 예시: `MySQL2024!@#`

#### 추가 사용자 계정 (선택)
```
User Name: news_app
Host: localhost
Role: DB Admin
Password: [나중에 설정]
```
- "Add User" 클릭하여 추가 (권장하지만 선택사항)
- "Next" 클릭

### 3.5 Windows Service (서비스 설정)
```
Configure MySQL Server as a Windows Service: ✅ 체크
Windows Service Name: MySQL80 (기본값)
Start the MySQL Server at System Startup: ✅ 체크 ⭐ 권장
Run Windows Service as: Standard System Account 선택
```
- "Next" 클릭

### 3.6 Server File Permissions
- **Yes, grant full access to the user running the Windows Service** 선택
- "Next" 클릭

### 3.7 설정 적용
- "Execute" 클릭하여 설정 적용
- 모든 단계에 ✅ 표시되면 "Finish" 클릭

## 📊 4단계: MySQL Workbench 설정

### 4.1 Connection 테스트
1. MySQL Workbench 실행 (시작 메뉴에서 검색)
2. "MySQL Connections"에서 "Local instance MySQL80" 클릭
3. Root 비밀번호 입력
4. 연결 성공 확인

### 4.2 기본 설정 확인
```sql
-- MySQL 버전 확인
SELECT VERSION();

-- 문자 인코딩 확인
SHOW VARIABLES LIKE 'character_set%';

-- 데이터베이스 목록 확인
SHOW DATABASES;
```

## 🖥️ 5단계: 명령줄(CMD) 설정

### 5.1 환경 변수 설정
1. **시작 메뉴** → **시스템 환경 변수 편집** 검색 후 실행
2. **환경 변수** 버튼 클릭
3. **시스템 변수**에서 **Path** 선택 후 **편집**
4. **새로 만들기** 클릭 후 다음 경로 추가:
   ```
   C:\Program Files\MySQL\MySQL Server 8.0\bin
   ```
5. **확인** 클릭하여 모든 창 닫기

### 5.2 명령줄 접속 테스트
1. **명령 프롬프트(CMD)** 또는 **PowerShell** 새로 실행
2. MySQL 접속 테스트:
   ```cmd
   mysql -u root -p
   ```
3. Root 비밀번호 입력
4. 성공 시 `mysql>` 프롬프트 표시

### 5.3 기본 명령어 확인
```sql
-- 버전 확인
SELECT VERSION();

-- 현재 사용자 확인
SELECT USER();

-- 나가기
EXIT;
```

## ⚠️ 6단계: 방화벽 설정 (선택사항)

### 6.1 Windows Defender 방화벽 규칙
외부에서 MySQL 접속이 필요한 경우:
1. **시작 메뉴** → **고급 보안이 포함된 Windows Defender 방화벽** 실행
2. **인바운드 규칙** → **새 규칙**
3. **포트** → **TCP** → **특정 로컬 포트 3306**
4. **연결 허용** → **모든 프로필** → 규칙 이름: "MySQL Server"

⚠️ **보안 주의**: 외부 접속은 보안 위험이 있으므로 개발 환경에서만 사용

## ✅ 7단계: 설치 확인

### 7.1 서비스 상태 확인
```cmd
# 서비스 관리자에서 확인
services.msc

# 또는 명령줄에서 확인
sc query MySQL80
```

### 7.2 포트 확인
```cmd
netstat -an | findstr :3306
```

### 7.3 연결 테스트
```cmd
mysql -u root -p -h localhost
```

## 🎯 다음 단계

1. **데이터베이스 초기화**: `setup_database.bat` 실행
2. **Python 연결 테스트**: `python 05_python_connection_test.py` 실행
3. **2회차 강의 코드** 실행 준비 완료

## 🔧 주요 설정 파일 위치

```
MySQL 설치 경로:
C:\Program Files\MySQL\MySQL Server 8.0\

설정 파일 (my.ini):
C:\ProgramData\MySQL\MySQL Server 8.0\my.ini

데이터 디렉토리:
C:\ProgramData\MySQL\MySQL Server 8.0\Data\

로그 파일:
C:\ProgramData\MySQL\MySQL Server 8.0\Data\[컴퓨터명].err
```

## ⚡ 빠른 문제 해결

| 문제 | 해결 방법 |
|------|-----------|
| **서비스가 시작되지 않음** | 서비스 관리자에서 MySQL80 서비스 수동 시작 |
| **포트 3306 사용 중** | `netstat -ano \| findstr :3306`으로 충돌 프로세스 확인 |
| **비밀번호 분실** | MySQL Installer → Reconfigure → Authentication Method 재설정 |
| **Workbench 연결 실패** | 방화벽 또는 바이러스 백신 프로그램 확인 |

---

**다음**: [데이터베이스 초기화 가이드](./04_database_setup.sql) | [문제 해결](./troubleshooting.md)
