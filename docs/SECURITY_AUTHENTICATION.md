# 보안 및 인증 시스템

## 개요

본 프로젝트는 **한국 정부 IT 서비스 보안 규정**을 준수하는 이메일 기반 회원 가입 및 인증 시스템을 구현했습니다.

## 주요 보안 기능

### 1. 비밀번호 보안

#### 비밀번호 복잡도 요구사항
- **최소 길이**: 8자 이상
- **최대 길이**: 128자 이하
- **문자 조합**: 영문 대소문자, 숫자, 특수문자 중 **3가지 이상** 조합
- **금지 패턴**:
  - 연속된 숫자 3개 이상 (예: 123, 234)
  - 연속된 알파벳 3개 이상 (예: abc, ABC)
  - 동일 문자 3개 이상 연속 (예: aaa, 111)

#### 비밀번호 암호화
- **해싱 알고리즘**: bcrypt
- **솔트(Salt)**: 자동 생성
- **복호화 불가능**: 단방향 해싱으로 원본 비밀번호 복구 불가

### 2. 계정 보안

#### 로그인 보안
- **최대 로그인 시도 횟수**: 5회
- **계정 잠금 시간**: 30분
- **실패 횟수 추적**: 데이터베이스에 저장
- **성공 시 초기화**: 로그인 성공 시 실패 횟수 0으로 초기화

#### 계정 상태 관리
- **is_active**: 계정 활성화 여부
- **is_verified**: 이메일 인증 여부
- **locked_until**: 계정 잠금 해제 시간

### 3. JWT 토큰 인증

#### 토큰 구조
- **액세스 토큰**: 30분 유효 (짧은 수명)
- **리프레시 토큰**: 7일 유효 (긴 수명)
- **알고리즘**: HS256 (HMAC with SHA-256)

#### 토큰 페이로드
```json
{
  "sub": "사용자 ID",
  "email": "사용자 이메일",
  "exp": "만료 시간 (Unix timestamp)"
}
```

### 4. 이메일 인증

#### 인증 프로세스
1. 회원 가입 시 임의의 보안 토큰 생성 (32바이트 URL-safe)
2. 이메일로 인증 링크 전송
3. 사용자가 링크 클릭하여 인증 완료
4. 인증 토큰 만료: 24시간

#### 미인증 사용자 처리
- 현재는 미인증 사용자도 로그인 가능 (선택적)
- 필요 시 `auth.py` 라우터에서 주석 해제하여 강제 가능

### 5. 입력 검증 및 XSS 방지

#### 이메일 검증
- **EmailStr**: Pydantic의 이메일 검증
- **정제(Sanitize)**: 소문자 변환, 공백 제거

#### 이름 검증
- **HTML 태그 제거**: 정규식으로 모든 HTML 태그 제거
- **최대 길이**: 100자

### 6. SQL Injection 방지

- **ORM 사용**: SQLAlchemy를 통한 파라미터화된 쿼리
- **직접 SQL 사용 금지**: 모든 데이터베이스 작업은 ORM을 통해 수행

### 7. CORS 보안

- **허용된 출처만 접근 가능**: `settings.CORS_ORIGINS`에 정의된 도메인만 허용
- **자격 증명 포함**: `allow_credentials=True`

## API 엔드포인트

### 회원 가입
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecureP@ssw0rd!",
  "full_name": "홍길동"
}
```

**응답** (201 Created):
```json
{
  "message": "회원 가입이 완료되었습니다.",
  "detail": "이메일 인증을 완료해주세요."
}
```

### 로그인
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecureP@ssw0rd!"
}
```

**응답** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 토큰 갱신
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 이메일 인증
```http
POST /api/auth/verify-email
Content-Type: application/json

{
  "token": "abc123def456ghi789..."
}
```

### 현재 사용자 정보 조회
```http
GET /api/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**응답** (200 OK):
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "홍길동",
  "is_active": true,
  "is_verified": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login_at": "2024-01-02T12:00:00Z"
}
```

## 환경 변수 설정

`.env` 파일에 다음 설정을 추가하세요:

```bash
# JWT 설정
SECRET_KEY=your-super-secret-key-change-this-in-production-must-be-at-least-32-characters-long
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 이메일 설정 (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=News Sentiment AI

# 프론트엔드 URL
FRONTEND_URL=http://localhost:3000
```

### Gmail SMTP 설정 방법

1. **2단계 인증 활성화**
   - Google 계정 설정 > 보안 > 2단계 인증 활성화

2. **앱 비밀번호 생성**
   - Google 계정 설정 > 보안 > 앱 비밀번호
   - "메일" 및 "기타" 선택
   - 생성된 16자리 비밀번호를 `SMTP_PASSWORD`에 입력

## 데이터베이스 마이그레이션

```bash
# 백엔드 디렉토리로 이동
cd backend

# 의존성 설치
pip install -r ../requirements.txt

# FastAPI 애플리케이션 실행 (자동으로 테이블 생성)
uvicorn app.main:app --reload
```

## 보안 체크리스트

### 운영 환경 배포 전 확인사항

- [ ] `SECRET_KEY` 변경 (최소 32자 이상의 랜덤 문자열)
- [ ] `.env` 파일을 `.gitignore`에 추가 (이미 추가됨)
- [ ] HTTPS 사용 (SSL/TLS 인증서 설정)
- [ ] CORS 설정을 실제 도메인으로 제한
- [ ] 데이터베이스 비밀번호 강화
- [ ] SMTP 계정 보안 (앱 비밀번호 사용)
- [ ] 로그 모니터링 설정
- [ ] 비밀번호 정책 사용자에게 안내
- [ ] 이메일 인증 강제 여부 결정
- [ ] 비밀번호 재설정 기능 추가 (선택사항)

## 추가 보안 기능 (권장)

### 1. Rate Limiting
- FastAPI의 `slowapi`를 사용하여 API 요청 제한
- 로그인, 회원가입 엔드포인트에 적용 권장

### 2. CAPTCHA
- reCAPTCHA v3를 회원가입/로그인에 추가
- 봇 공격 방지

### 3. 2단계 인증 (2FA)
- TOTP (Time-based One-Time Password) 구현
- Google Authenticator, Authy 등 지원

### 4. 비밀번호 재설정
- 이메일을 통한 비밀번호 재설정 링크 전송
- 재설정 토큰 1시간 유효

### 5. 감사 로그 (Audit Log)
- 모든 인증 관련 이벤트 로깅
- 로그인 성공/실패, 비밀번호 변경 등

## 문제 해결

### 이메일이 전송되지 않는 경우
1. SMTP 설정 확인
2. Gmail의 경우 "보안 수준이 낮은 앱 허용" 비활성화 확인
3. 앱 비밀번호 사용 확인
4. 방화벽에서 SMTP 포트(587) 허용 확인

### 토큰 검증 실패
1. `SECRET_KEY`가 변경되지 않았는지 확인
2. 토큰 만료 시간 확인
3. 시스템 시간 동기화 확인 (NTP)

### 계정 잠금 해제
```sql
-- MySQL에서 직접 계정 잠금 해제
UPDATE users
SET failed_login_attempts = 0, locked_until = NULL
WHERE email = 'user@example.com';
```

## 참고 자료

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [JWT 공식 문서](https://jwt.io/)
- [FastAPI 보안 가이드](https://fastapi.tiangolo.com/tutorial/security/)
- [한국인터넷진흥원(KISA) 보안 가이드](https://www.kisa.or.kr/)
