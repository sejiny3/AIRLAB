# 강의 슬라이드 생성기

`../UNBOLT_workshop.pptx`(154장)를 만드는 코드입니다. 슬라이드 내용을 고칠 때는 PowerPoint에서 직접 고쳐도 되지만,
여기를 고치고 다시 만들면 디자인(색, 배치, 글꼴)이 전체에서 일관되게 유지됩니다.

| 파일 | 내용 |
|---|---|
| `lib.js` | 테마 색, 레이아웃(제목/섹션/본문), 공통 부품(카드, 코드 상자, "비유·왜·성공·안 되면" 상자, 퀴즈, 요약) |
| `s0_intro.js` | 시작하기 (일정, 환경, ROS 2 용어, 진행 방식) |
| `s0b_install.js` | 설치 (Windows 점검, WSL + Ubuntu, 설치 스크립트, ~/.bashrc 환경 설정, 빌드, 점검, 첫 실행, 대시보드, API 키) |
| `s1_bridge.js` ~ `s4_llm.js` | 모듈 1~4 |
| `s5_end.js` | 마무리, 부록 (오류 TOP 8, 명령 모음) |
| `render_assets.py` | MuJoCo로 로봇·방·헤드 카메라 그림을 `assets/`에 렌더링 |
| `assets/` | 렌더링한 그림 + 대시보드 스크린샷 (`../../../docs/`의 그림도 씀) |

## 다시 만들기

Windows(Node.js 18 이상)에서:

```bash
cd workshop/slides/src
npm install
node build.js            # → ../UNBOLT_workshop.pptx
```

그림을 다시 렌더링하려면 WSL Ubuntu에서 (MuJoCo, OpenCV 필요):

```bash
python3 ~/unbolt/workshop/slides/src/render_assets.py
```

`dashboard_idle.png`는 대시보드를 켠 상태(1440×1000)에서 찍은 스크린샷입니다.

## 고칠 때 주의

- 발표자 노트는 각 `content(제목, 태그, 노트)`의 세 번째 인자, 퀴즈 정답은 `quiz()`가 노트에 자동으로 넣습니다.
- 한글이 글자 단위로 끊기지 않게 `lib.js`의 `write()`가 모든 문단을 단어 단위 줄바꿈(`eaLnBrk="0"`, `ko-KR`)으로 바꿉니다.
- 도형 크기가 음수가 되면 PowerPoint가 파일 전체를 열지 못합니다. `write()`가 이것을 찾아 오류로 멈춥니다.
- 맑은 고딕에서는 `\`가 `₩`로 보이니, 역슬래시가 들어가는 명령은 `code()` 상자(Consolas)에 넣으세요.
