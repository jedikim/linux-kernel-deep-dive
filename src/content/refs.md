## 일차 자료 {#primary}

- [리눅스 커널 소스 v7.3](https://github.com/torvalds/linux/tree/v7.3): 이 책의 모든 코드 인용이 나온 곳.
- [docs.kernel.org](https://docs.kernel.org/): 소스 트리의 `Documentation/`을 그대로 실은 공식 문서.
- [lore.kernel.org](https://lore.kernel.org/): 메일링 리스트 보관소. 패치와 그 토론이 모두 남아 있습니다.
- [man7.org](https://man7.org/linux/man-pages/): 시스템 콜과 커널 인터페이스의 매뉴얼 페이지.
- [elixir.bootlin.com](https://elixir.bootlin.com/linux/v7.3/source): 식별자를 따라가며 읽는 소스 브라우저.

## 변화를 따라가는 곳 {#news}

- [LWN.net 커널 색인](https://lwn.net/Kernel/Index/): 주제별로 정리된 커널 기사. 설계 논의의 배경을 알기에 가장 좋습니다.
- [Kernel Newbies: LinuxVersions](https://kernelnewbies.org/LinuxVersions): 버전마다 무엇이 들어왔는지의 요약.
- [kernel.org](https://www.kernel.org/): 메인라인, 안정 버전, 장기 지원 버전의 현재 목록.

## 강의와 글 {#articles}

- Kernel of Linux 강의 교안. 공개SW 역량프라자 OLC의 모델 커리큘럼 과정 교재입니다. CC BY 2.0 KR, © Korea OSS Promotion Forum, NIPA.
- [문c 블로그](http://jake.dothome.co.kr/): 커널 소스를 함수 단위로 따라가며 해설한 한국어 글 모음. 이 책과 관련 깊은 글로 [선점과 컨텍스트 스위치](http://jake.dothome.co.kr/preemption/), [틱 디바이스](http://jake.dothome.co.kr/tick-device/), [top-half와 bottom-half](http://jake.dothome.co.kr/two-part-interrupt-handler/), [우선순위 역전과 상속](http://jake.dothome.co.kr/priority-inheritance/), [RCU](http://jake.dothome.co.kr/rcu/)가 있습니다.
- [linux-insides](https://github.com/0xAX/linux-insides): 부팅, 인터럽트, 시스템 콜, 타이머를 소스로 따라가는 책.
- [Linux Kernel Labs](https://linux-kernel-labs.github.io/refs/heads/master/): 강의 자료와 실습. [SMP 강의](https://linux-kernel-labs.github.io/refs/heads/master/lectures/smp.html)가 동시성의 좋은 입문입니다.
- Eli Bendersky, [Launching Linux threads and processes with clone](https://eli.thegreenplace.net/2018/launching-linux-threads-and-processes-with-clone/): 스레드와 프로세스가 `clone` 플래그의 차이임을 예제로 보입니다.
- Jiannan Ouyang, [Kernel Level Concurrency: Locks and Kernel Preemption](http://people.cs.pitt.edu/~ouyang/20150225-kernel-concurreny.html): 락, 선점 끄기, 인터럽트 끄기의 관계.
- Matt Fleming, [Linux kernel preemption and the latency-throughput tradeoff](https://www.codeblueprint.co.uk/2019/12/23/linux-preemption-latency-throughput.html): 선점 모델별 측정.
- Alex Dzyoba, [Basic x86 interrupts](https://alex.dzyoba.com/blog/os-interrupts/): 작은 커널에서 IDT와 PIC를 직접 설정해 보는 글.
- [Interactive map of Linux kernel](https://makelinux.github.io/kernel/map/): 서브시스템과 주요 함수의 지도.
- Brendan Gregg, [Linux Performance](https://www.brendangregg.com/linuxperf.html): 관측 도구의 지도와 사용법.

## 책 {#books}

- Robert Love, *Linux Kernel Development* (3판, 2010). 커널 전반의 입문서. 버전은 오래되었지만 설명의 뼈대는 여전히 좋습니다.
- Daniel P. Bovet, Marco Cesati, *Understanding the Linux Kernel* (3판, 2005).
- Wolfgang Mauerer, *Professional Linux Kernel Architecture* (2008).
- Michael Kerrisk, *The Linux Programming Interface* (2010). 유저 공간에서 본 커널 인터페이스.
- Paul E. McKenney, [*Is Parallel Programming Hard, And, If So, What Can You Do About It?*](https://mirrors.edge.kernel.org/pub/linux/kernel/people/paulmck/perfbook/perfbook.html): RCU를 만든 사람이 쓴 병렬 프로그래밍 책. 무료로 공개되어 있습니다.
- Brendan Gregg, *Systems Performance* (2판, 2020), *BPF Performance Tools* (2019).
