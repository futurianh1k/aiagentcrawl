# Freemium 모델 사용자 플로우

## 개요

본 프로젝트는 Freemium 비즈니스 모델을 적용하여, 비로그인 사용자에게도 제한적인 기능을 제공하면서 로그인을 통해 전체 기능을 이용할 수 있도록 설계되었습니다.

## 사용자 유형별 기능 비교

| 기능 | 비로그인 사용자 | 로그인 사용자 |
|------|----------------|--------------|
| 뉴스 검색 | ✅ 최대 3개 기사 | ✅ 최대 50개 기사 |
| 감정 분석 | ✅ 기본 분석 | ✅ 전체 분석 |
| 검색 이력 | ❌ | ✅ 저장 및 조회 |
| CSV 내보내기 | ❌ | ✅ |
| JSON 내보내기 | ❌ | ✅ |
| AI 종합 요약 | ✅ 제한적 | ✅ 전체 |
| 토큰 사용량 조회 | ❌ | ✅ |

## 사용자 플로우

### 비로그인 사용자 플로우

```
1. 랜딩 페이지 접속
   ↓
2. "로그인 없이 계속하기" 클릭 또는 직접 검색
   ↓
3. 키워드 입력 및 검색 (자동으로 3개로 제한됨)
   ↓
4. 기본 감정 분석 결과 확인
   ↓
5. "더 많은 기사를 보려면 로그인" 배너 표시
   ↓
6. [회원가입] 또는 [로그인] 버튼 클릭
   ↓
7. 회원가입 / 로그인 후 전체 기능 이용
```

### 로그인 사용자 플로우

```
1. 로그인 또는 회원가입
   ↓
2. 대시보드 접속
   ↓
3. 무제한 검색 (최대 50개)
   ↓
4. 전체 감정 분석 + AI 요약
   ↓
5. 검색 이력 자동 저장
   ↓
6. CSV/JSON 내보내기
   ↓
7. 토큰 사용량 통계 조회
```

## 백엔드 구현

### 1. 선택적 인증 (Optional Authentication)

#### backend/app/api/dependencies.py

```python
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    선택적 인증 - 토큰이 있으면 검증, 없으면 None 반환
    비로그인 사용자도 접근 가능한 API에 사용
    """
    if not credentials:
        return None

    payload = verify_token(credentials.credentials)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    return user if user and user.is_active else None
```

### 2. Freemium 로직 적용

#### backend/app/api/routes/agents.py

```python
# Freemium 설정
MAX_ARTICLES_FREE = 3  # 비로그인 사용자 최대 기사 수
MAX_ARTICLES_PREMIUM = 50  # 로그인 사용자 최대 기사 수

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_news(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user_optional),  # 선택적 인증
    agent_service: NewsAnalysisAgent = Depends(get_agent_service),
    db: Session = Depends(get_database_session)
):
    """
    뉴스 감정 분석 시작

    Freemium 모델:
    - 비로그인: 최대 3개 기사
    - 로그인: 최대 50개 기사 + 검색 이력 저장
    """
    # Freemium 로직: 비로그인 사용자 제한
    actual_max_articles = request.max_articles
    is_premium_user = current_user is not None

    if not is_premium_user:
        # 비로그인 사용자는 최대 3개로 제한
        if actual_max_articles > MAX_ARTICLES_FREE:
            actual_max_articles = MAX_ARTICLES_FREE
    else:
        # 로그인 사용자는 최대 50개로 제한
        if actual_max_articles > MAX_ARTICLES_PREMIUM:
            actual_max_articles = MAX_ARTICLES_PREMIUM

    # 검색 이력 저장 (로그인 사용자만)
    if is_premium_user:
        # 검색 이력 저장 로직...
        pass

    # 분석 세션 생성 (user_id 저장)
    session = AnalysisSession(
        user_id=current_user.id if current_user else None,
        keyword=request.keyword,
        sources=json.dumps(request.sources),
        status="processing"
    )
    # ...
```

### 3. 데이터베이스 모델 수정

#### backend/app/models/database.py

```python
class AnalysisSession(Base):
    """분석 세션 모델"""
    __tablename__ = "analysis_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # NULL = 비로그인 사용자
    keyword = Column(String(255), nullable=False, index=True)
    # ...

    # 관계 설정
    user = relationship("User", backref="analysis_sessions")
    articles = relationship("Article", back_populates="session")
```

## 프론트엔드 구현

### 1. 인증 컨텍스트

#### frontend/contexts/AuthContext.tsx

```typescript
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 로컬 스토리지에서 토큰 로드
  useEffect(() => {
    const loadUser = async () => {
      const savedToken = localStorage.getItem('access_token');
      if (savedToken) {
        const userData = await authApi.getCurrentUser(savedToken);
        setUser(userData);
        setToken(savedToken);
      }
    };
    loadUser();
  }, []);

  // ...
}
```

### 2. 로그인/회원가입 페이지

- `/app/auth/login/page.tsx` - 로그인 페이지
- `/app/auth/register/page.tsx` - 회원가입 페이지
- 둘 다 "로그인 없이 계속하기" 링크 제공

### 3. API 호출 시 토큰 전달

#### frontend/lib/api.ts

```typescript
export const newsApi = {
  // 뉴스 감정 분석 시작 (선택적 인증)
  analyzeNews: async (data: AnalysisRequest, token?: string): Promise<AnalysisResponse> => {
    const config = token ? {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    } : {};
    const response = await api.post('/api/agents/analyze', data, config);
    return response.data;
  },
  // ...
}
```

## 보안 고려사항

### 백엔드

1. **인증 토큰 검증**: JWT 토큰을 사용하여 안전하게 사용자 인증
2. **입력값 검증**: Pydantic 스키마로 모든 입력값 검증
3. **SQL Injection 방지**: SQLAlchemy ORM 사용
4. **XSS 방지**: 입력값 정제 (sanitize)

### 프론트엔드

1. **토큰 저장**: 로컬 스토리지에 저장 (보안상 HttpOnly Cookie 권장)
2. **자동 로그아웃**: 토큰 만료 시 자동 로그아웃
3. **HTTPS 사용**: 운영 환경에서 필수

## 향후 개선 사항

### 추가 기능 아이디어

1. **유료 플랜 추가**
   - Basic (무료): 3개 기사
   - Pro ($9.99/월): 50개 기사 + 모든 기능
   - Enterprise ($29.99/월): 무제한 + API 접근

2. **기능별 접근 제어**
   - 미디어 다운로드 (Pro 이상)
   - 고급 AI 분석 (Enterprise)
   - API 키 발급 (Enterprise)

3. **사용량 제한**
   - 일일 검색 횟수 제한
   - 월간 토큰 사용량 제한
   - Rate Limiting 강화

4. **사용자 경험 개선**
   - 실시간 사용량 표시
   - 업그레이드 권장 배너
   - 무료 체험 기간 제공

## 테스트 방법

### 백엔드 테스트

```bash
# 비로그인 사용자 검색 (3개 제한)
curl -X POST http://localhost:8000/api/agents/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "AI",
    "sources": ["naver"],
    "max_articles": 10
  }'

# 로그인 사용자 검색 (50개까지)
curl -X POST http://localhost:8000/api/agents/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "keyword": "AI",
    "sources": ["naver"],
    "max_articles": 10
  }'
```

### 프론트엔드 테스트

1. 비로그인 상태에서 대시보드 접속
2. 10개 기사 검색 시도 → 3개만 반환되는지 확인
3. 로그인 후 10개 기사 검색 → 10개 모두 반환되는지 확인
4. 검색 이력이 저장되는지 확인

## 결론

Freemium 모델을 통해:
- ✅ 진입 장벽을 낮춰 사용자 획득 용이
- ✅ 서비스 가치를 먼저 경험 후 회원가입
- ✅ 로그인 전환율 향상
- ✅ 남용 방지 (최대 3개 제한)
- ✅ 명확한 업그레이드 인센티브

상세한 보안 문서는 `docs/SECURITY_AUTHENTICATION.md`를 참고하세요.
