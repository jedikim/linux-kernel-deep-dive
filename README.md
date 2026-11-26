# 리눅스 커널 깊이 읽기

소스 코드로 따라가는 운영체제의 구조와 개발 방법론 · Linux v7.3 기준

**https://jedikim.github.io/linux-kernel-deep-dive/**

| 부 | 장 |
|---|---|
| 0부 길잡이 | 0 커널이라는 프로그램 |
| 1부 태스크 | 1 fork: 한 번 부르고 두 번 돌아온다 · 2 task_struct와 스레드 · 3 태스크의 상태와 대기 |
| 2부 스케줄러 | 4 스케줄러의 뼈대 · 5 CFS에서 EEVDF로 · 6 커널 선점 · 7 멀티코어 스케줄링 |
| 3부 시간과 인터럽트 | 8 시간과 타이머 · 9 인터럽트 하드웨어 · 10 커널의 IRQ 계층 · 11 Top half와 Bottom half · 12 패킷 하나의 여정 |
| 4부 동시성 | 13 경쟁 조건과 실행 컨텍스트 · 14 스핀락과 뮤텍스 · 15 우선순위 역전과 상속 · 16 RCU |
| 5부 메모리 | 17 가상 주소 공간 · 18 물리 메모리와 회수 |
| 6부 시스템 콜과 I/O | 19 시스템 콜 · 20 VFS와 파일시스템 · 21 블록 계층과 io_uring |
| 7부 격리와 확장 | 22 네임스페이스와 cgroup · 23 가상화와 KVM · 24 eBPF |
| 8부 개발 방법론 | 25 C로 쓴 객체지향 · 26 커널은 어떻게 만들어지는가 · 27 품질을 지키는 장치 · 28 직접 해 보기 |

Jedi Kim — [LinkedIn](https://www.linkedin.com/in/jedikim/) · [jedikim.com](https://jedikim.com)

본문에 인용한 리눅스 커널 소스는 [GPL-2.0](https://github.com/torvalds/linux/blob/v7.3/COPYING)을 따릅니다.

## 빌드

```bash
python3 src/build.py
```

원고는 `src/content/`, 그림은 `src/fig/`에 있습니다. `pandoc`과 Python 3(`beautifulsoup4`)가 필요합니다.
