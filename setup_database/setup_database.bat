@echo off
REM ============================================================================
REM MySQL 데이터베이스 자동 설치 스크립트 (Windows)
REM 
REM 목적: 2회차 강의 - AI 에이전트 기반 뉴스 감정분석 시스템
REM 지원: Windows 10/11
REM 
REM 이 스크립트는 다음을 수행합니다:
REM 1. MySQL 서비스 상태 확인
REM 2. 데이터베이스 초기화 SQL 실행
REM 3. Python 패키지 설치 확인
REM 4. 연결 테스트
REM 
REM 사용법: setup_database.bat
REM ============================================================================

setlocal enabledelayedexpansion

REM 색상 및 스타일 정의 (Windows 10/11 지원)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "MAGENTA=[95m"
set "CYAN=[96m"
set "WHITE=[97m"
set "RESET=[0m"

REM 로그 함수들 (배치에서는 함수 대신 라벨 사용)

:log_info
echo %BLUE%[INFO]%RESET% %~1
goto :eof

:log_success
echo %GREEN%[SUCCESS]%RESET% %~1
goto :eof

:log_warning
echo %YELLOW%[WARNING]%RESET% %~1
goto :eof

:log_error
echo %RED%[ERROR]%RESET% %~1
goto :eof

:log_header
echo.
echo %CYAN%============================================%RESET%
echo %CYAN% %~1%RESET%
echo %CYAN%============================================%RESET%
goto :eof

REM 메인 스크립트 시작
:main
call :log_header "MySQL 데이터베이스 자동 설치 스크립트"
echo %MAGENTA%2회차 강의: AI 에이전트 기반 뉴스 감정분석 시스템%RESET%
echo.

REM 1. MySQL 서비스 상태 확인
call :check_mysql_service
if errorlevel 1 (
    call :log_error "MySQL 서비스를 사용할 수 없습니다"
    call :log_info "MySQL 설치 가이드를 참고하여 MySQL을 먼저 설치하세요"
    pause
    exit /b 1
)

REM 2. 사용자 입력 받기
call :get_database_credentials

REM 3. Root 연결 테스트
call :test_mysql_connection "%DB_HOST%" "%DB_ROOT_USER%" "%DB_ROOT_PASSWORD%"
if errorlevel 1 (
    call :log_error "Root 사용자로 MySQL에 연결할 수 없습니다"
    call :log_info "사용자명과 비밀번호를 확인하세요"
    pause
    exit /b 1
)

REM 4. SQL 스크립트 실행
call :execute_sql_script
if errorlevel 1 (
    call :log_error "데이터베이스 초기화에 실패했습니다"
    call :log_info "수동으로 04_database_setup.sql 파일을 실행해보세요"
    pause
    exit /b 1
)

REM 5. 최종 연결 테스트
call :final_connection_test
if errorlevel 1 (
    call :log_error "최종 연결 테스트에 실패했습니다"
    pause
    exit /b 1
)

REM 6. Python 패키지 확인
call :check_python_packages

REM 7. 설정 요약
call :print_summary

REM 8. Python 연결 테스트 실행 (선택)
echo.
set /p "run_test=Python 연결 테스트를 실행하시겠습니까? (Y/n): "
if /i not "%run_test%"=="n" (
    call :run_python_test
)

call :log_success "MySQL 데이터베이스 설정이 완료되었습니다!"
pause
exit /b 0

REM ============================================================================
REM 함수 구현부
REM ============================================================================

:check_mysql_service
call :log_header "MySQL 서비스 상태 확인"

REM MySQL80 서비스 확인
sc query MySQL80 >nul 2>&1
if !errorlevel! equ 0 (
    sc query MySQL80 | findstr "RUNNING" >nul
    if !errorlevel! equ 0 (
        call :log_success "MySQL80 서비스가 실행 중입니다"
        goto :eof
    ) else (
        call :log_warning "MySQL80 서비스가 중지되어 있습니다"
        call :log_info "MySQL80 서비스 시작 시도..."

        net start MySQL80 >nul 2>&1
        if !errorlevel! equ 0 (
            call :log_success "MySQL80 서비스를 시작했습니다"
            goto :eof
        ) else (
            call :log_error "MySQL80 서비스 시작 실패"
            exit /b 1
        )
    )
)

REM MySQL 서비스 확인 (일반적인 이름)
sc query MySQL >nul 2>&1
if !errorlevel! equ 0 (
    sc query MySQL | findstr "RUNNING" >nul
    if !errorlevel! equ 0 (
        call :log_success "MySQL 서비스가 실행 중입니다"
        goto :eof
    ) else (
        call :log_warning "MySQL 서비스가 중지되어 있습니다"
        call :log_info "MySQL 서비스 시작 시도..."

        net start MySQL >nul 2>&1
        if !errorlevel! equ 0 (
            call :log_success "MySQL 서비스를 시작했습니다"
            goto :eof
        )
    )
)

REM 포트 3306 확인
netstat -an | findstr :3306 >nul 2>&1
if !errorlevel! equ 0 (
    call :log_success "MySQL이 포트 3306에서 실행 중입니다"
    goto :eof
)

call :log_error "MySQL 서비스를 찾을 수 없습니다"
call :log_info "MySQL이 설치되어 있는지 확인하세요"
exit /b 1

:test_mysql_connection
set "host=%~1"
set "user=%~2"
set "password=%~3"

call :log_info "MySQL 연결 테스트: %user%@%host%"

mysql -h "%host%" -u "%user%" -p"%password%" -e "SELECT 1;" >nul 2>&1
if !errorlevel! equ 0 (
    call :log_success "MySQL 연결 성공"
    exit /b 0
) else (
    call :log_error "MySQL 연결 실패"
    exit /b 1
)

:get_database_credentials
call :log_header "데이터베이스 연결 정보 입력"

echo MySQL Root 사용자 정보를 입력하세요:
echo.

set /p "DB_HOST=Host (기본값: localhost): "
if "%DB_HOST%"=="" set "DB_HOST=localhost"

set /p "DB_PORT=Port (기본값: 3306): "
if "%DB_PORT%"=="" set "DB_PORT=3306"

set /p "DB_ROOT_USER=Root Username (기본값: root): "
if "%DB_ROOT_USER%"=="" set "DB_ROOT_USER=root"

REM 비밀번호 숨김 입력 (Windows에서는 제한적)
call :log_info "Root Password를 입력하세요 (입력이 보이지 않음):"
powershell -command "$pwd = read-host -AsSecureString; $ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($pwd); $result = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr); [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr); $result" > temp_pwd.txt
set /p DB_ROOT_PASSWORD=<temp_pwd.txt
del temp_pwd.txt

set /p "DB_APP_USER=새 사용자명 (기본값: news_app): "
if "%DB_APP_USER%"=="" set "DB_APP_USER=news_app"

call :log_info "새 사용자 비밀번호를 입력하세요:"
powershell -command "$pwd = read-host -AsSecureString; $ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($pwd); $result = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr); [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr); if ($result -eq '') { 'secure_password_here' } else { $result }" > temp_pwd2.txt
set /p DB_APP_PASSWORD=<temp_pwd2.txt
del temp_pwd2.txt
if "%DB_APP_PASSWORD%"=="" set "DB_APP_PASSWORD=secure_password_here"

set /p "DB_NAME=데이터베이스명 (기본값: news_sentiment_analysis): "
if "%DB_NAME%"=="" set "DB_NAME=news_sentiment_analysis"

echo.
call :log_info "설정 완료: %DB_APP_USER%@%DB_HOST%:%DB_PORT%/%DB_NAME%"
goto :eof

:execute_sql_script
call :log_header "데이터베이스 초기화 SQL 실행"

set "sql_file=04_database_setup.sql"

if not exist "%sql_file%" (
    call :log_error "SQL 스크립트 파일을 찾을 수 없습니다: %sql_file%"
    call :log_info "현재 디렉토리에 %sql_file% 파일이 있는지 확인하세요"
    exit /b 1
)

call :log_info "SQL 스크립트 파일 발견: %sql_file%"

REM 임시 SQL 파일 생성 (비밀번호 치환)
set "temp_sql=%TEMP%\setup_database_temp.sql"

REM PowerShell을 사용하여 문자열 치환
call :log_info "비밀번호 설정 및 SQL 스크립트 준비 중..."
powershell -command "(Get-Content '%sql_file%') -replace 'secure_password_here', '%DB_APP_PASSWORD%' | Set-Content '%temp_sql%'"

call :log_info "MySQL에 연결하여 SQL 스크립트 실행 중..."

mysql -h "%DB_HOST%" -P "%DB_PORT%" -u "%DB_ROOT_USER%" -p"%DB_ROOT_PASSWORD%" < "%temp_sql%"
if !errorlevel! equ 0 (
    call :log_success "데이터베이스 초기화 완료"
    del "%temp_sql%" 2>nul
    exit /b 0
) else (
    call :log_error "SQL 스크립트 실행 실패"
    call :log_info "수동으로 실행해보세요: mysql -u %DB_ROOT_USER% -p < %sql_file%"
    del "%temp_sql%" 2>nul
    exit /b 1
)

:check_python_packages
call :log_header "Python 패키지 확인"

set "packages=mysql-connector-python sqlalchemy pymysql pandas requests beautifulsoup4 selenium textblob transformers"
set "missing_packages="

for %%p in (%packages%) do (
    python -c "import %%p" >nul 2>&1
    if !errorlevel! neq 0 (
        REM beautifulsoup4는 bs4로 import해야 함
        if "%%p"=="beautifulsoup4" (
            python -c "import bs4" >nul 2>&1
            if !errorlevel! equ 0 (
                call :log_success "%%p 설치됨"
            ) else (
                call :log_warning "%%p 누락"
                set "missing_packages=!missing_packages! %%p"
            )
        ) else (
            REM mysql-connector-python은 mysql.connector로 import
            if "%%p"=="mysql-connector-python" (
                python -c "import mysql.connector" >nul 2>&1
                if !errorlevel! equ 0 (
                    call :log_success "%%p 설치됨"
                ) else (
                    call :log_warning "%%p 누락"
                    set "missing_packages=!missing_packages! %%p"
                )
            ) else (
                call :log_warning "%%p 누락"
                set "missing_packages=!missing_packages! %%p"
            )
        )
    ) else (
        call :log_success "%%p 설치됨"
    )
)

if "%missing_packages%"=="" (
    call :log_success "모든 필수 패키지가 설치되어 있습니다"
    goto :eof
)

call :log_warning "누락된 패키지:%missing_packages%"
set /p "install_packages=누락된 패키지를 설치하시겠습니까? (y/N): "

if /i "%install_packages%"=="y" (
    call :log_info "패키지 설치 중..."
    for %%p in (%missing_packages%) do (
        call :log_info "설치 중: %%p"
        pip install "%%p"
        if !errorlevel! equ 0 (
            call :log_success "%%p 설치 완료"
        ) else (
            call :log_error "%%p 설치 실패"
        )
    )
) else (
    call :log_info "패키지 설치를 건너뜁니다"
    call :log_info "나중에 수동으로 설치하세요: pip install%missing_packages%"
)
goto :eof

:final_connection_test
call :log_header "최종 연결 테스트"

call :log_info "새로 생성된 사용자로 연결 테스트 중..."

call :test_mysql_connection "%DB_HOST%" "%DB_APP_USER%" "%DB_APP_PASSWORD%"
if !errorlevel! equ 0 (
    call :log_success "사용자 '%DB_APP_USER%' 연결 성공"

    REM 테이블 존재 확인
    for /f "tokens=*" %%a in ('mysql -h "%DB_HOST%" -P "%DB_PORT%" -u "%DB_APP_USER%" -p"%DB_APP_PASSWORD%" -D "%DB_NAME%" -e "SHOW TABLES;" 2^>nul ^| find /c /v ""') do set table_count=%%a

    if !table_count! gtr 1 (
        set /a actual_count=!table_count!-1
        call :log_success "데이터베이스 테이블 확인: !actual_count!개"
    ) else (
        call :log_warning "테이블이 생성되지 않았습니다"
    )

    exit /b 0
) else (
    call :log_error "사용자 '%DB_APP_USER%' 연결 실패"
    call :log_info "MySQL 설정을 확인하고 다시 시도하세요"
    exit /b 1
)

:run_python_test
call :log_header "Python 연결 테스트 실행"

set "python_test_file=05_python_connection_test.py"

if exist "%python_test_file%" (
    call :log_info "Python 연결 테스트 스크립트를 실행합니다..."
    call :log_info "테스트 스크립트에서 연결 정보를 입력하세요"
    echo.

    python "%python_test_file%"
) else (
    call :log_warning "Python 연결 테스트 파일을 찾을 수 없습니다: %python_test_file%"
    call :log_info "수동으로 연결을 테스트해보세요"
)
goto :eof

:print_summary
call :log_header "설정 완료 요약"

echo %WHITE%데이터베이스 연결 정보:%RESET%
echo   Host: %DB_HOST%
echo   Port: %DB_PORT%
echo   Database: %DB_NAME%
echo   User: %DB_APP_USER%
echo   Password: [설정됨]
echo.

echo %WHITE%다음 단계:%RESET%
echo   1. Python 연결 테스트: python 05_python_connection_test.py
echo   2. 2회차 강의 코드 실행
echo   3. 문제 발생 시: troubleshooting.md 참고
echo.

echo %WHITE%연결 문자열 (SQLAlchemy):%RESET%
echo   mysql+pymysql://%DB_APP_USER%:[PASSWORD]@%DB_HOST%:%DB_PORT%/%DB_NAME%?charset=utf8mb4
goto :eof
