"""
예제 1: Playwright 환경 설정 및 기본 사용법

2회차 강의: AI 에이전트 기반 뉴스 감성 분석 시스템
Playwright 기본 설정과 브라우저 관리 실습
"""

import asyncio
import time
from datetime import datetime

from crawlers.playwright_basic import PlaywrightManager, ContextualCrawler
from config.settings import settings


async def example_basic_setup():
    """기본 Playwright 설정 예제"""
    print("🎭 Playwright 기본 설정 예제")
    print("=" * 50)

    # PlaywrightManager 사용
    async with PlaywrightManager() as manager:
        print(f"✅ 브라우저 타입: {settings.crawler.browser_type}")
        print(f"✅ 헤드리스 모드: {settings.crawler.headless}")

        # 기본 컨텍스트 생성
        context = await manager.create_context()
        print("✅ 기본 컨텍스트 생성 완료")

        # 페이지 생성 및 테스트
        page = await context.new_page()

        # 간단한 웹사이트 방문
        test_url = "https://httpbin.org/html"
        print(f"🌐 테스트 URL 방문: {test_url}")

        start_time = time.time()
        await page.goto(test_url)
        load_time = time.time() - start_time

        # 페이지 정보 추출
        title = await page.title()
        print(f"📄 페이지 제목: {title}")
        print(f"⏱️ 로드 시간: {load_time:.2f}초")

        # 페이지 정리
        await page.close()
        await manager.cleanup_context(context)


async def example_contextual_crawler():
    """ContextualCrawler 사용 예제"""
    print("\n🕷️ ContextualCrawler 사용 예제")
    print("=" * 50)

    async with ContextualCrawler() as crawler:
        # 단일 URL 크롤링
        test_url = "https://httpbin.org/json"
        print(f"🎯 단일 URL 크롤링: {test_url}")

        result = await crawler.crawl_url(test_url)

        if result['success']:
            print("✅ 크롤링 성공!")
            print(f"   - URL: {result['url']}")
            print(f"   - 제목: {result['title']}")
            print(f"   - 응답 상태: {result['response_status']}")
            print(f"   - 콘텐츠 길이: {len(result['content'])} 문자")
        else:
            print(f"❌ 크롤링 실패: {result['error']}")


async def example_multiple_contexts():
    """다중 컨텍스트 사용 예제"""
    print("\n🔄 다중 컨텍스트 사용 예제")
    print("=" * 50)

    async with PlaywrightManager() as manager:
        # 일반 컨텍스트
        context1 = await manager.create_context()
        print("✅ 컨텍스트 1 생성 (일반)")

        # 스텔스 컨텍스트
        context2 = await manager.create_stealth_context()
        print("✅ 컨텍스트 2 생성 (스텔스)")

        # 각 컨텍스트에서 페이지 생성
        page1 = await context1.new_page()
        page2 = await context2.new_page()

        # 동시에 다른 페이지 방문
        tasks = [
            page1.goto("https://httpbin.org/user-agent"),
            page2.goto("https://httpbin.org/headers")
        ]

        start_time = time.time()
        await asyncio.gather(*tasks)
        parallel_time = time.time() - start_time

        print(f"⚡ 병렬 로딩 시간: {parallel_time:.2f}초")

        # User-Agent 비교
        content1 = await page1.content()
        content2 = await page2.content()

        print("🔍 컨텍스트별 설정 확인:")
        print(f"   - 컨텍스트 1 콘텐츠 길이: {len(content1)} 문자")
        print(f"   - 컨텍스트 2 콘텐츠 길이: {len(content2)} 문자")

        # 정리
        await page1.close()
        await page2.close()
        await manager.cleanup_context(context1)
        await manager.cleanup_context(context2)


async def example_error_handling():
    """오류 처리 예제"""
    print("\n⚠️ 오류 처리 예제")
    print("=" * 50)

    async with ContextualCrawler() as crawler:
        # 잘못된 URL 테스트
        invalid_urls = [
            "https://invalid-domain-12345.com",
            "https://httpbin.org/status/404",
            "https://httpbin.org/delay/10"  # 타임아웃 테스트
        ]

        for url in invalid_urls:
            print(f"🧪 테스트 URL: {url}")
            result = await crawler.crawl_url(url, wait_for_load_state="domcontentloaded")

            if result['success']:
                print(f"   ✅ 성공: 상태 {result['response_status']}")
            else:
                print(f"   ❌ 실패: {result['error_type']} - {result['error']}")


async def example_performance_comparison():
    """성능 비교 예제"""
    print("\n📊 성능 비교 예제")
    print("=" * 50)

    test_urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/json", 
        "https://httpbin.org/xml",
    ]

    async with ContextualCrawler() as crawler:
        # 순차 처리
        print("🐌 순차 처리 테스트...")
        start_time = time.time()

        sequential_results = []
        for url in test_urls:
            result = await crawler.crawl_url(url)
            sequential_results.append(result)

        sequential_time = time.time() - start_time

        # 병렬 처리
        print("🚀 병렬 처리 테스트...")
        start_time = time.time()

        parallel_results = await crawler.crawl_multiple_urls(
            test_urls, 
            max_concurrent=3,
            delay_between_requests=0.1
        )

        parallel_time = time.time() - start_time

        # 결과 비교
        print(f"\n📈 성능 비교 결과:")
        print(f"   - 순차 처리: {sequential_time:.2f}초")
        print(f"   - 병렬 처리: {parallel_time:.2f}초")
        print(f"   - 개선율: {sequential_time/parallel_time:.1f}배")

        # 성공률 확인
        sequential_success = sum(1 for r in sequential_results if r.get('success', False))
        parallel_success = sum(1 for r in parallel_results if r.get('success', False))

        print(f"\n✅ 성공률:")
        print(f"   - 순차 처리: {sequential_success}/{len(test_urls)} ({sequential_success/len(test_urls)*100:.1f}%)")
        print(f"   - 병렬 처리: {parallel_success}/{len(test_urls)} ({parallel_success/len(test_urls)*100:.1f}%)")


async def main():
    """메인 실행 함수"""
    print("🎭 Playwright 환경 설정 및 기본 사용법")
    print("2회차 강의 - 예제 1")
    print("=" * 60)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        await example_basic_setup()
        await example_contextual_crawler()
        await example_multiple_contexts()
        await example_error_handling()
        await example_performance_comparison()

        print("\n🎉 모든 예제가 성공적으로 완료되었습니다!")

    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n📚 다음 예제: python examples/02_context_pages.py")


if __name__ == "__main__":
    # 이벤트 루프 설정 (Windows 호환성)
    if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
