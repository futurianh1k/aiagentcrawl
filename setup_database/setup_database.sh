#!/bin/bash
# ============================================================================
# MySQL 데이터베이스 자동 설치 스크립트 (Linux/Mac)
# 
# 목적: 2회차 강의 - AI 에이전트 기반 뉴스 감정분석 시스템
# 지원: Ubuntu 20.04+, macOS 11+
# 
# 이 스크립트는 다음을 수행합니다:
# 1. MySQL 서비스 상태 확인
# 2. 데이터베이스 초기화 SQL 실행
# 3. Python 패키지 설치 확인
# 4. 연결 테스트
# 
# 사용법:
#   chmod +x setup_database.sh
#   ./setup_database.sh
# ============================================================================

set -e  # 오류 발생 시 스크립트 중단

# 색상 코드 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 로그 함수들
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo
    echo -e "${CYAN}============================================${NC}"
    echo -e "${CYAN} $1${NC}"
    echo -e "${CYAN}============================================${NC}"
}

# 운영체제 감지
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/lsb-release ]; then
            OS="ubuntu"
            log_info "Ubuntu 시스템 감지"
        else
            OS="linux"
            log_info "Linux 시스템 감지"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        log_info "macOS 시스템 감지"
    else
        OS="unknown"
        log_error "지원하지 않는 운영체제입니다: $OSTYPE"
        exit 1
    fi
}

# MySQL 서비스 상태 확인
check_mysql_service() {
    log_header "MySQL 서비스 상태 확인"

    if [[ "$OS" == "ubuntu" || "$OS" == "linux" ]]; then
        if systemctl is-active --quiet mysql; then
            log_success "MySQL 서비스가 실행 중입니다"
            return 0
        elif systemctl is-active --quiet mysqld; then
            log_success "MySQL 서비스가 실행 중입니다 (mysqld)"
            return 0
        else
            log_warning "MySQL 서비스가 실행되지 않습니다"
            log_info "MySQL 서비스 시작 시도..."

            if sudo systemctl start mysql 2>/dev/null || sudo systemctl start mysqld 2>/dev/null; then
                log_success "MySQL 서비스를 시작했습니다"
                return 0
            else
                log_error "MySQL 서비스를 시작할 수 없습니다"
                log_error "MySQL이 설치되어 있는지 확인하세요"
                return 1
            fi
        fi

    elif [[ "$OS" == "macos" ]]; then
        if brew services list | grep -q "mysql.*started"; then
            log_success "MySQL 서비스가 실행 중입니다 (Homebrew)"
            return 0
        elif pgrep -x "mysqld" > /dev/null; then
            log_success "MySQL 서버가 실행 중입니다"
            return 0
        else
            log_warning "MySQL 서비스가 실행되지 않습니다"
            log_info "MySQL 서비스 시작 시도..."

            if command -v brew >/dev/null 2>&1; then
                if brew services start mysql; then
                    log_success "MySQL 서비스를 시작했습니다 (Homebrew)"
                    sleep 3  # 서비스 시작 대기
                    return 0
                else
                    log_error "MySQL 서비스 시작 실패"
                    return 1
                fi
            else
                log_error "Homebrew를 찾을 수 없습니다. MySQL을 수동으로 시작하세요"
                return 1
            fi
        fi
    fi
}

# MySQL 연결 테스트
test_mysql_connection() {
    local host="$1"
    local user="$2"
    local password="$3"

    log_info "MySQL 연결 테스트: $user@$host"

    if mysql -h "$host" -u "$user" -p"$password" -e "SELECT 1;" >/dev/null 2>&1; then
        log_success "MySQL 연결 성공"
        return 0
    else
        log_error "MySQL 연결 실패"
        return 1
    fi
}

# 사용자 입력 받기
get_database_credentials() {
    log_header "데이터베이스 연결 정보 입력"

    echo "MySQL Root 사용자 정보를 입력하세요:"
    echo

    read -p "Host (기본값: localhost): " DB_HOST
    DB_HOST=${DB_HOST:-localhost}

    read -p "Port (기본값: 3306): " DB_PORT
    DB_PORT=${DB_PORT:-3306}

    read -p "Root Username (기본값: root): " DB_ROOT_USER
    DB_ROOT_USER=${DB_ROOT_USER:-root}

    read -s -p "Root Password: " DB_ROOT_PASSWORD
    echo

    read -p "새 사용자명 (기본값: news_app): " DB_APP_USER
    DB_APP_USER=${DB_APP_USER:-news_app}

    read -s -p "새 사용자 비밀번호 (기본값: secure_password_here): " DB_APP_PASSWORD
    DB_APP_PASSWORD=${DB_APP_PASSWORD:-secure_password_here}
    echo

    read -p "데이터베이스명 (기본값: news_sentiment_analysis): " DB_NAME
    DB_NAME=${DB_NAME:-news_sentiment_analysis}

    echo
    log_info "설정 완료: $DB_APP_USER@$DB_HOST:$DB_PORT/$DB_NAME"
}

# SQL 스크립트 실행
execute_sql_script() {
    log_header "데이터베이스 초기화 SQL 실행"

    local sql_file="04_database_setup.sql"

    if [ ! -f "$sql_file" ]; then
        log_error "SQL 스크립트 파일을 찾을 수 없습니다: $sql_file"
        log_info "현재 디렉토리에 $sql_file 파일이 있는지 확인하세요"
        return 1
    fi

    log_info "SQL 스크립트 파일 발견: $sql_file"

    # 임시 SQL 파일 생성 (비밀번호 치환)
    local temp_sql="/tmp/setup_database_temp.sql"

    # SQL 파일에서 비밀번호 치환
    sed "s/secure_password_here/$DB_APP_PASSWORD/g" "$sql_file" > "$temp_sql"

    log_info "MySQL에 연결하여 SQL 스크립트 실행 중..."

    if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_ROOT_USER" -p"$DB_ROOT_PASSWORD" < "$temp_sql"; then
        log_success "데이터베이스 초기화 완료"
        rm -f "$temp_sql"
        return 0
    else
        log_error "SQL 스크립트 실행 실패"
        log_info "수동으로 실행해보세요: mysql -u $DB_ROOT_USER -p < $sql_file"
        rm -f "$temp_sql"
        return 1
    fi
}

# Python 패키지 확인
check_python_packages() {
    log_header "Python 패키지 확인"

    local packages=(
        "mysql-connector-python"
        "sqlalchemy"
        "pymysql"
        "pandas"
        "requests"
        "beautifulsoup4"
        "selenium"
        "textblob"
        "transformers"
    )

    local missing_packages=()

    for package in "${packages[@]}"; do
        if python3 -c "import ${package//-/_}" 2>/dev/null || python3 -c "import ${package//4/}" 2>/dev/null; then
            log_success "$package 설치됨"
        else
            log_warning "$package 누락"
            missing_packages+=("$package")
        fi
    done

    if [ ${#missing_packages[@]} -eq 0 ]; then
        log_success "모든 필수 패키지가 설치되어 있습니다"
        return 0
    else
        log_warning "누락된 패키지: ${missing_packages[*]}"

        read -p "누락된 패키지를 설치하시겠습니까? (y/N): " install_packages

        if [[ "$install_packages" =~ ^[Yy]$ ]]; then
            log_info "패키지 설치 중..."

            for package in "${missing_packages[@]}"; do
                log_info "설치 중: $package"
                if pip3 install "$package"; then
                    log_success "$package 설치 완료"
                else
                    log_error "$package 설치 실패"
                fi
            done
        else
            log_info "패키지 설치를 건너뜁니다"
            log_info "나중에 수동으로 설치하세요: pip3 install ${missing_packages[*]}"
        fi
    fi
}

# 최종 연결 테스트
final_connection_test() {
    log_header "최종 연결 테스트"

    log_info "새로 생성된 사용자로 연결 테스트 중..."

    if test_mysql_connection "$DB_HOST" "$DB_APP_USER" "$DB_APP_PASSWORD"; then
        log_success "사용자 '$DB_APP_USER' 연결 성공"

        # 테이블 존재 확인
        local table_count
        table_count=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_APP_USER" -p"$DB_APP_PASSWORD" -D "$DB_NAME" -e "SHOW TABLES;" 2>/dev/null | wc -l)

        if [ "$table_count" -gt 1 ]; then  # 헤더 제외
            log_success "데이터베이스 테이블 확인: $((table_count-1))개"
        else
            log_warning "테이블이 생성되지 않았습니다"
        fi

        return 0
    else
        log_error "사용자 '$DB_APP_USER' 연결 실패"
        log_info "MySQL 설정을 확인하고 다시 시도하세요"
        return 1
    fi
}

# Python 연결 테스트 실행
run_python_test() {
    log_header "Python 연결 테스트 실행"

    local python_test_file="05_python_connection_test.py"

    if [ -f "$python_test_file" ]; then
        log_info "Python 연결 테스트 스크립트를 실행합니다..."
        log_info "테스트 스크립트에서 연결 정보를 입력하세요"
        echo

        python3 "$python_test_file"
    else
        log_warning "Python 연결 테스트 파일을 찾을 수 없습니다: $python_test_file"
        log_info "수동으로 연결을 테스트해보세요"
    fi
}

# 설정 요약 출력
print_summary() {
    log_header "설정 완료 요약"

    echo -e "${WHITE}데이터베이스 연결 정보:${NC}"
    echo "  Host: $DB_HOST"
    echo "  Port: $DB_PORT"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_APP_USER"
    echo "  Password: [설정됨]"
    echo

    echo -e "${WHITE}다음 단계:${NC}"
    echo "  1. Python 연결 테스트: python3 05_python_connection_test.py"
    echo "  2. 2회차 강의 코드 실행"
    echo "  3. 문제 발생 시: troubleshooting.md 참고"
    echo

    echo -e "${WHITE}연결 문자열 (SQLAlchemy):${NC}"
    echo "  mysql+pymysql://$DB_APP_USER:[PASSWORD]@$DB_HOST:$DB_PORT/$DB_NAME?charset=utf8mb4"
}

# 메인 함수
main() {
    log_header "MySQL 데이터베이스 자동 설치 스크립트"
    echo -e "${MAGENTA}2회차 강의: AI 에이전트 기반 뉴스 감정분석 시스템${NC}"
    echo

    # 1. 운영체제 감지
    detect_os

    # 2. MySQL 서비스 확인
    if ! check_mysql_service; then
        log_error "MySQL 서비스를 사용할 수 없습니다"
        log_info "MySQL 설치 가이드를 참고하여 MySQL을 먼저 설치하세요"
        exit 1
    fi

    # 3. 사용자 입력
    get_database_credentials

    # 4. Root 연결 테스트
    if ! test_mysql_connection "$DB_HOST" "$DB_ROOT_USER" "$DB_ROOT_PASSWORD"; then
        log_error "Root 사용자로 MySQL에 연결할 수 없습니다"
        log_info "사용자명과 비밀번호를 확인하세요"
        exit 1
    fi

    # 5. SQL 스크립트 실행
    if ! execute_sql_script; then
        log_error "데이터베이스 초기화에 실패했습니다"
        log_info "수동으로 04_database_setup.sql 파일을 실행해보세요"
        exit 1
    fi

    # 6. 최종 연결 테스트
    if ! final_connection_test; then
        log_error "최종 연결 테스트에 실패했습니다"
        exit 1
    fi

    # 7. Python 패키지 확인
    check_python_packages

    # 8. 설정 요약
    print_summary

    # 9. Python 연결 테스트 실행 (선택)
    echo
    read -p "Python 연결 테스트를 실행하시겠습니까? (Y/n): " run_test
    if [[ ! "$run_test" =~ ^[Nn]$ ]]; then
        run_python_test
    fi

    log_success "MySQL 데이터베이스 설정이 완료되었습니다!"
}

# 스크립트 실행
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
