# 캐릭터 후보 풀 — 생성 프롬프트 40장

> **이 40장이 캐릭터 8종의 원천이 된다.** 여기서 서로 가장 먼 8명을 골라
> 캐릭터로 쓰고, 나머지 32장은 스타일 평균(μ_style) 추정에 쓴다.
> 한 번의 생성으로 두 가지가 동시에 해결된다.

## 왜 이렇게 바꿨나 — 1단계에서 측정한 것

캐릭터 8종을 **얼굴 특징 축으로 설계**했더니(얼굴 길이 × 하관 폭 × 이목구비 간격),
SFace 임베딩에서 **무작위로 고른 것보다 나쁘게** 뭉쳤다.

| | 잔차 최대 쌍 |
|---|---|
| 현재 캐릭터 8종 (설계) | **0.714** — 무작위 선정보다 나쁨 (하위 11%) |
| 40장 풀에서 무작위 8명 (중앙값) | 0.560 |
| 40장 풀에서 max-min 선정 8명 | **0.248** |

이유는 명확하다. 세 축 중 둘을 공유하는 쌍(예: 03·04는 이목구비 간격만 다르다)이
사실상 같은 벡터가 된다. **SFace가 '이목구비 간격'을 거의 인코딩하지 않기 때문**이다.
사람 눈에는 다른 얼굴이지만 모델에게는 같은 얼굴이다.

무작위로 골라도 0.36 미만이 나올 확률은 1.8%뿐이다. 즉 **설계로도 운으로도 안 되고,
측정해서 골라야 한다.**

## 생성 규칙 — 이것만 지키면 된다

1. **공통 스타일 블록을 40장 전부에 글자 하나 바꾸지 말고 붙일 것.**
   아래 블록은 기존 캐릭터 8종의 실제 모습(정장·흰 셔츠·남색 넥타이)에 맞춰
   `character-prompts.md`에서 수정된 것이다. 이제 이쪽이 기준이다.
2. **네거티브 프롬프트도 동일하게.**
3. **한 장씩 다른 시드로.** 같은 얼굴이 겹치면 그쪽으로 평균이 쏠린다.
4. **마음에 안 들어도 재생성 금지.** 고르는 순간 사람 취향이 들어가 표본이
   편향된다. 얼굴이 아예 안 나온 경우만 다시 뽑는다. **어느 8명이 캐릭터가 될지는
   스크립트가 정한다.**
5. **개별 파일로, 캐릭터와 같은 해상도로.** 격자 시트 한 장으로 뽑으면 얼굴당
   해상도가 200px 안팎이라 화면·인쇄용으로 부족하다. 1086×1448(3:4) 기준.
6. 최소 24장, **권장 40장**. 많을수록 선정 품질이 올라간다.

## 넣을 위치

```
assets/pool/pool_01.png ... pool_40.png     ← 01~20 남성, 21~40 여성 (번호 순서 유지)
```

번호 순서가 남녀 4:4 정원 제약에 쓰이므로 **묘사 번호와 파일 번호를 맞출 것.**

넣은 뒤:

```bash
./.venv/bin/python scripts/select_characters.py            # 선정 결과 확인
./.venv/bin/python scripts/select_characters.py --apply    # 반영
./.venv/bin/python scripts/build_prototypes.py
./.venv/bin/python scripts/similarity_matrix.py
```

---

## 공통 스타일 블록 (40장 전부 동일)

> **의상 문구가 바뀌었다.** 기존 8종은 정장·흰 셔츠·넥타이로 생성됐는데
> `character-prompts.md`의 블록은 "남색 셔츠 깃만"이라고 적혀 있어 서로 어긋나 있었다.
> 실측에서 μ_style·μ_char = 0.760으로 스타일 불일치가 확인됐다(1.0에 가까워야 정상).
> 사원증에는 정장 쪽이 어울리므로 **정장으로 통일**한다.

```
Photorealistic corporate ID badge portrait of a Korean adult in their mid-20s.
Studio headshot, straight-on frontal view, camera exactly at eye level, head and
shoulders only, head centered and filling about 70% of the frame height.
Seamless light grey (#F0F0F2) studio backdrop, evenly lit with no visible shadow
on the background. Soft frontal key light from a large softbox with subtle fill,
no harsh shadows on the face, neutral white balance around 5500K. Neutral
expression with a very subtle closed-lip smile, eyes looking directly into the
lens. Wearing a dark navy suit jacket over a white collared shirt with a navy
tie, only the shoulders and upper chest visible at the bottom edge of the frame.
Evenly sharp across the entire face, shot on an 85mm lens at f/5.6, no lens
distortion. 3:4 vertical aspect ratio, high resolution, natural skin texture with
visible pores, no beauty retouching.
```

## 공통 네거티브 프롬프트

```
wide-angle distortion, fisheye, tilted head, three-quarter view, profile view,
dramatic side lighting, colored gel lighting, hard shadows, busy background,
dark background, hat, heavy makeup, large earrings, necklace, hands, full body,
multiple people, text, watermark, logo, oversaturated, plastic airbrushed skin
```

---

## 얼굴 묘사 40종

각 줄을 **공통 스타일 블록 앞에** 붙인다.

### 남성 20 (01~20)

```
01  A man with a round full face, soft undefined jawline, small close-set eyes, flat wide nose, thick straight brows, very short buzzed black hair.
02  A man with a narrow rectangular face, prominent chin, deep-set hooded eyes, long straight nose, medium black hair parted in the middle.
03  A man with a broad heart-shaped face, wide forehead tapering to a narrow chin, large double-eyelid eyes, short black hair with a low fade. Wearing thin silver rectangular glasses.
04  A man with a heavy square face, thick neck, wide-set monolid eyes, short flat nose, close-cropped black hair, slight stubble shadow.
05  A man with a long oval face, high cheekbones, slightly downturned eyes, narrow nose bridge, black hair swept to the right.
06  A man with a compact triangular face, sharp pointed chin, thin arched brows, wide-set almond eyes, black hair with textured fringe over the forehead.
07  A man with an angular diamond-shaped face, hollow cheeks, deep-set eyes, aquiline nose, very short black hair. Wearing thick black round glasses.
08  A man with a wide flat face, low forehead, small eyes with single eyelids, broad short nose, black hair combed straight back.
09  A man with a slender oval face, soft rounded jaw, large gentle eyes, small straight nose, medium-length black hair tucked behind the ears.
10  A man with a boxy face and a strong protruding jaw, thick lips, bushy brows, wide-set eyes, short black crew cut.
11  A man with a long narrow face, prominent nose, thin lips, closely set eyes, receding hairline with short black hair.
12  A man with a round soft face, chubby cheeks, small round nose, crescent-shaped smiling eyes, black bowl-cut hair. Wearing thin gold wire glasses.
13  A man with a chiseled rectangular face, defined cheekbones, straight thick brows, medium-set eyes, black hair in a short side part.
14  A man with a broad oval face, wide-set large eyes, flat nose bridge, full lips, shoulder-length black hair tied back.
15  A man with a narrow angular face, pointed chin, narrow-set deep eyes, long thin nose, short spiky black hair.
16  A man with a square-jawed face and a very wide mouth, thick straight brows, small eyes, short black hair with a clean side fade.
17  A man with a soft rounded face, low cheekbones, drooping outer eye corners, small mouth, medium black hair with a center part. Wearing rimless glasses.
18  A man with a tall narrow face, high forehead, narrow-set eyes, thin arched brows, long straight nose, short black hair.
19  A man with a wide oval face, broad cheekbones, thick lower lip, large round eyes, black hair with loose curls.
20  A man with an elongated face, sharp jawline, hooded monolid eyes, high nose bridge, very short black hair with a shaved side.
```

### 여성 20 (21~40)

```
21  A woman with a round full face, soft small chin, large round double-eyelid eyes, small button nose, straight black hair to the shoulders.
22  A woman with a long narrow face, high cheekbones, narrow-set almond eyes, thin straight nose, black hair in a tight bun.
23  A woman with a heart-shaped face, wide forehead, pointed chin, wide-set large eyes, short black pixie cut.
24  A woman with a square face, defined jaw, straight thick brows, medium-set monolid eyes, chin-length black bob with blunt bangs. Wearing thin black rectangular glasses.
25  A woman with an oval face, gentle rounded jaw, upward-slanting eyes, small delicate nose, long black hair parted on the side.
26  A woman with a wide flat face, low nose bridge, closely set small eyes, full round cheeks, black hair in twin low braids.
27  A woman with a slender diamond-shaped face, sharp cheekbones, deep-set eyes, narrow nose, black hair in a sleek high ponytail.
28  A woman with a short rounded face, soft jaw, large wide-set eyes, short philtrum, curly shoulder-length black hair. Wearing round tortoiseshell glasses.
29  A woman with a long oval face, narrow chin, hooded eyes, straight medium nose, very long straight black hair past the chest.
30  A woman with a broad square face, strong jawline, thick straight brows, medium almond eyes, black hair in a shoulder-length layered cut.
31  A woman with a small compact face, tiny pointed chin, very large round eyes, small nose, black hair in a short blunt bob.
32  A woman with a tall narrow face, high forehead, closely set eyes, long slim nose, thin lips, black hair pulled into a low bun.
33  A woman with a round soft face, full cheeks, crescent smiling eyes, small flat nose, black hair with straight-across bangs. Wearing thin silver oval glasses.
34  A woman with an angular oval face, prominent cheekbones, wide-set narrow eyes, defined nose bridge, black hair in a side-swept long cut.
35  A woman with a wide heart-shaped face, broad forehead, large double-eyelid eyes, small mouth, black hair in loose waves to the shoulders.
36  A woman with a long rectangular face, straight jawline, medium-set monolid eyes, straight nose, black hair in a straight center-parted long cut.
37  A woman with a petite rounded face, soft undefined jaw, downturned outer eye corners, small round nose, black hair in a messy short crop.
38  A woman with a slender long face, sharp V-shaped chin, upward-slanting narrow eyes, high nose bridge, black hair in a sleek middle-parted long style. Wearing thin rimless glasses.
39  A woman with a broad oval face, wide cheekbones, large wide-set eyes, full lips, black hair in a shoulder-length shag cut.
40  A woman with a compact square face, defined jaw, closely set almond eyes, short straight nose, black hair in a high tight ponytail.
```

---

## 여성 묘사의 의상 처리

21~40번 묘사에는 헤어스타일만 적혀 있고 의상은 공통 블록이 담당한다.
공통 블록의 정장 문구가 남녀 모두에 적용되면 된다 — 여성용 별도 문구는 필요 없다.

## 생성 후 확인

`select_characters.py`가 40장 중 서로 가장 먼 8명을 골라 캐릭터로 확정하고,
나머지 32장으로 μ_style을 계산한다. 선정된 8종이 자기 평균에 끼지 않으므로
1차 시도에서 문제였던 자기 센터링 편향이 생기지 않는다.

기대 수치는 **최대 쌍 0.30 미만**이다(40장 풀 실측에서 0.248 달성).

여기서도 0.36을 넘으면 후보를 60~80장으로 늘린다. 그래도 안 되면 캐릭터 문제가
아니라 **매칭 축 문제**이므로 SFace 대신 랜드마크 기반 기하 특징으로 전환을
검토한다. 다만 40장 실측이 0.248이었으므로 그럴 가능성은 낮다.
