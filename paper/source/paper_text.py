"""The draft's text. Numbers from the trial come in through `m`; nothing here is typed by hand from a log."""

TBD = '[측정 필요]'
TITLE_KO = ['이동 양팔 로봇의 물체 집기를 위한 역기구학 기반 기법과', '시각-언어-행동 정책의 시뮬레이션 성능 비교']
TITLE_EN = ('Simulation-Based Performance Comparison of Inverse Kinematics Grasping and '
            'Vision-Language-Action Policies for a Mobile Bimanual Robot')
RUNNING = '이동 양팔 로봇의 집기를 위한 역기구학 기법과 시각-언어-행동 정책의 성능 비교'
AUTHORS_KO = '[저자1]^{*}·[저자2]^{*}·[교신저자]^{*†}'
AFFIL_KO = '* [소속 기관 및 학과]'
AUTHORS_EN = '[Author 1]^{*}, [Author 2]^{*} and [Corresponding Author]^{*†}'
AFFIL_EN = ['* [Department, University]', '']
RECEIVED = '(Received [접수일] ; Revised [수정일] ; Accepted [채택일])'
EMAIL = ' [교신저자 이메일]'
KEYWORDS = ('Mobile Manipulation(이동 조작), Inverse Kinematics(역기구학), Imitation Learning(모방 학습), '
            'Vision-Language-Action Model(시각-언어-행동 모델), Robot Grasping(로봇 파지)')


def abstract_ko(m):
    return (f'이동 양팔 로봇의 상자 집기에서 마커와 역기구학을 쓰는 기존 방식(IK)과 두 시각-언어-행동 정책을 같은 시뮬레이션에서 '
            f'비교하였다. 정책은 노트북 CPU에서 처음부터 학습한 CNN 모델과 LoRA로 미세조정한 π0.5이며, 같은 시연 1,155개로 학습하였다. '
            f'처음 보는 100개 장면에서 두 정책 모두 100% 성공하였고, ROS 전체 스택의 집기 성공률은 IK {m["ik_rate"]}, '
            f'CNN {m["cnn_rate"]}, π0.5 {m["pi05_rate"]}이었다. 그러나 시연에 없던 단어나 한국어로 명령하거나 조명과 테이블 색을 '
            f'바꾸면 CNN의 성공률은 크게 떨어진 반면 π0.5는 거의 모두 성공하였고, 이 차이는 영상 증강을 맞추어도 줄지 않았다. 세 상자 중 하나를 문장으로 '
            f'고르는 과제에서는 π0.5만 색 낱말을 상자와 연결하여, 시연에서 뺀 색-자리 조합에서도 {m["row_pi05_L2"]} 성공하였다. '
            f'π0.5는 CNN이 본 학습 표본의 8분의 1로 같은 성공률에 이르렀고, 원격 GPU의 응답 지연 속에서도 전체 스택에서 실패하지 않았다.')


def abstract_en(m):
    return (f'This study compares three pick methods for a mobile bimanual robot in the same simulation: marker-based '
            f'inverse kinematics (IK), a small CNN policy trained on a laptop CPU, and π0.5 fine-tuned with LoRA. Both '
            f'policies learned from the same 1,155 demonstrations. On 100 unseen scenes both succeeded in every episode, '
            f'and through the full ROS stack picks succeeded {m["ik_rate"]} for IK, {m["cnn_rate"]} for the CNN policy '
            f'and {m["pi05_rate"]} for π0.5. With instructions made of unseen words or written in Korean, or with changed '
            f'lighting or table colour, however, the CNN policy fell sharply while π0.5 succeeded in almost every scene, '
            f'and matching the image augmentation did not close the gap. In a task that '
            f'chooses one of three boxes by the sentence, only π0.5 tied the colour words to the boxes, succeeding in '
            f'{m["row_pi05_L2"]} for a colour-slot combination left out of the demonstrations. π0.5 reached the same '
            f'success rate after seeing one eighth of the samples the CNN policy saw, and did not fail through the full '
            f'stack despite the latency of a remote GPU.')


NOTATION = [
    ('*{a}_{t}', '시각 *{t}의 관절 목표 벡터 (rad)'),
    ('*{s}_{t}', '시각 *{t}의 관절각 벡터 (rad)'),
    ('*{I}_{h}, *{I}_{w}', '머리 카메라, 손목 카메라 영상'),
    ('*{l}', '명령 문장'),
    ('*{H}', '행동 청크 길이 (10 단계)'),
    ('*{d}_{t}', '집기 종료 여부'),
    ('*{J}', '말단 자세에 대한 자코비안'),
    ('*{e}', '말단 자세 오차'),
    ('λ', '감쇠 계수'),
    ('τ', '흐름 정합의 보간 변수'),
]

REFS = [
    'Coleman, D., Sucan, I., Chitta, S. and Correll, N., 2014, "Reducing the Barrier to Entry of Complex Robotic Software: a MoveIt! Case Study," *{Journal of Software Engineering for Robotics}, Vol. 5, No. 1, pp. 3~16.',
    'Garrido-Jurado, S., Muñoz-Salinas, R., Madrid-Cuevas, F. J. and Marín-Jiménez, M. J., 2014, "Automatic Generation and Detection of Highly Reliable Fiducial Markers under Occlusion," *{Pattern Recognition}, Vol. 47, No. 6, pp. 2280~2292.',
    'Kuffner, J. J. and LaValle, S. M., 2000, "RRT-Connect: An Efficient Approach to Single-Query Path Planning," *{Proc. of IEEE Int. Conf. on Robotics and Automation}, San Francisco, CA, USA, Vol. 2, pp. 995~1001.',
    'Kim, H.-C., Yoon, I.-H. and Song, J.-B., 2021, "Deep Learning-based Pose Estimation for Mobile Manipulator Tasks," *{Trans. Korean Soc. Mech. Eng. A}, Vol. 45, No. 12, pp. 1161~1166.',
    'Levine, S., Finn, C., Darrell, T. and Abbeel, P., 2016, "End-to-End Training of Deep Visuomotor Policies," *{Journal of Machine Learning Research}, Vol. 17, No. 39, pp. 1~40.',
    'Zhao, T. Z., Kumar, V., Levine, S. and Finn, C., 2023, "Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware," *{Proc. of Robotics: Science and Systems XIX}, Daegu, Korea.',
    'Chi, C., Xu, Z., Feng, S., Cousineau, E., Du, Y., Burchfiel, B., Tedrake, R. and Song, S., 2025, "Diffusion Policy: Visuomotor Policy Learning via Action Diffusion," *{The International Journal of Robotics Research}, Vol. 44, No. 10-11, pp. 1684~1704.',
    'Black, K., Brown, N., Driess, D., Esmail, A., Equi, M. R., Finn, C., Fusai, N., Groom, L., Hausman, K., Ichter, B., Jakubczak, S., Jones, T., Ke, L., Levine, S., Li-Bell, A., Mothukuri, M., Nair, S., Pertsch, K., Shi, L. X., Smith, L., Tanner, J., Vuong, Q., Walling, A., Wang, H. and Zilinsky, U., 2025, "π0: A Vision-Language-Action Flow Model for General Robot Control," *{Proc. of Robotics: Science and Systems XXI}, Los Angeles, CA, USA.',
    'Black, K., Brown, N., Darpinian, J., Dhabalia, K., Driess, D., Esmail, A., Equi, M. R., Finn, C., Fusai, N., Galliker, M. Y., Ghosh, D., Groom, L., Hausman, K., Ichter, B., Jakubczak, S., Jones, T., Ke, L., LeBlanc, D., Levine, S., Li-Bell, A., Mothukuri, M., Nair, S., Pertsch, K., Ren, A. Z., Shi, L. X., Smith, L., Springenberg, J. T., Stachowicz, K., Tanner, J., Vuong, Q., Walke, H., Walling, A., Wang, H., Yu, L. and Zilinsky, U., 2025, "π0.5: A Vision-Language-Action Model with Open-World Generalization," arXiv preprint arXiv:2504.16054.',
    'Todorov, E., Erez, T. and Tassa, Y., 2012, "MuJoCo: A Physics Engine for Model-Based Control," *{Proc. of IEEE/RSJ Int. Conf. on Intelligent Robots and Systems}, Vilamoura-Algarve, Portugal, pp. 5026~5033.',
    'Macenski, S., Foote, T., Gerkey, B., Lalancette, C. and Woodall, W., 2022, "Robot Operating System 2: Design, Architecture, and Uses in the Wild," *{Science Robotics}, Vol. 7, No. 66, eabm6074.',
    'Macenski, S., Martín, F., White, R. and Clavero, J. G., 2020, "The Marathon 2: A Navigation System," *{Proc. of IEEE/RSJ Int. Conf. on Intelligent Robots and Systems}, Las Vegas, NV, USA, pp. 2718~2725.',
    'Nakamura, Y. and Hanafusa, H., 1986, "Inverse Kinematic Solutions with Singularity Robustness for Robot Manipulator Control," *{Journal of Dynamic Systems, Measurement, and Control}, Vol. 108, No. 3, pp. 163~171.',
    'Laskey, M., Lee, J., Fox, R., Dragan, A. and Goldberg, K., 2017, "DART: Noise Injection for Robust Imitation Learning," *{Proc. of the 1st Annual Conf. on Robot Learning}, Mountain View, CA, USA, PMLR Vol. 78, pp. 143~156.',
    'Beyer, L., Steiner, A., Susano Pinto, A., Kolesnikov, A., Wang, X., Salz, D., Neumann, M., Alabdulmohsin, I., Tschannen, M., Bugliarello, E., Unterthiner, T., Keysers, D., Koppula, S., Liu, F., Grycner, A., Gritsenko, A., Houlsby, N., Kumar, M., Rong, K., Eisenschlos, J., Kabra, R., Bauer, M., Bošnjak, M., Chen, X., Minderer, M., Voigtlaender, P., Bica, I., Balazevic, I., Puigcerver, J., Papalampidi, P., Henaff, O., Xiong, X., Soricut, R., Harmsen, J. and Zhai, X., 2024, "PaliGemma: A Versatile 3B VLM for Transfer," arXiv preprint arXiv:2407.07726.',
    'Lipman, Y., Chen, R. T. Q., Ben-Hamu, H., Nickel, M. and Le, M., 2023, "Flow Matching for Generative Modeling," *{Proc. of Int. Conf. on Learning Representations}.',
    'Hu, E. J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., Wang, L. and Chen, W., 2022, "LoRA: Low-Rank Adaptation of Large Language Models," *{Proc. of Int. Conf. on Learning Representations}.',
    'Geirhos, R., Jacobsen, J.-H., Michaelis, C., Zemel, R., Brendel, W., Bethge, M. and Wichmann, F. A., 2020, "Shortcut Learning in Deep Neural Networks," *{Nature Machine Intelligence}, Vol. 2, No. 11, pp. 665~673.',
    'Wang, W., Wei, F., Dong, L., Bao, H., Yang, N. and Zhou, M., 2020, "MiniLM: Deep Self-Attention Distillation for Task-Agnostic Compression of Pre-Trained Transformers," *{Advances in Neural Information Processing Systems}, Vol. 33, pp. 5776~5788.',
    'Reimers, N. and Gurevych, I., 2019, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," *{Proc. of Conf. on Empirical Methods in Natural Language Processing and Int. Joint Conf. on Natural Language Processing}, Hong Kong, China, pp. 3982~3992.',
]


def body(m):
    """(kind, payload) items in document order."""
    B, C, S, I = 'body', 'chapter', 'section', 'item'
    return [
        (C, '1. 서 론'),
        (S, '1.1 연구 배경'),
        (B, '이동 조작 로봇은 주행과 팔 동작을 결합해 넓은 공간에서 물체를 다룬다. 현장에서 널리 쓰이는 집기 방식은 카메라로 물체의 자세를 구하고 역기구학(Inverse kinematics, IK)과 경로 계획으로 팔을 움직이는 것이다.^{(1~3)} 이 방식은 동작을 설명하기 쉽고 위치 정확도를 예측할 수 있으나, 물체마다 인식 수단과 파지 자세를 사람이 정해 주어야 한다. Kim 등^{(4)}은 이동 조작 로봇의 마커 자세 오차를 신경망으로 보정하여 이 방식의 정확도를 높였다.'),
        (B, '이와 달리 모방 학습은 영상과 관절각에서 행동을 바로 예측하는 정책을 시연으로 학습한다.^{(5~7)} 최근에는 영상과 문장을 함께 입력받는 시각-언어-행동(Vision-Language-Action, VLA) 모델이 제안되었고, π0와 π0.5는 여러 로봇의 데이터로 사전 학습한 가중치를 새 로봇에 미세조정하는 방법을 보였다.^{(8,9)} 그러나 이런 대형 모델이 단일 작업에서 작은 정책이나 기존 IK 방식보다 얼마나 나은지는 작업과 비용에 따라 달라지므로, 같은 조건에서 비교한 자료가 필요하다.'),
        (S, '1.2 연구 목적'),
        (B, '본 연구는 이동 양팔 로봇의 상자 집기 작업에서 세 방식을 같은 시뮬레이션 환경으로 비교한다. 첫째는 ArUco 마커와 IK를 쓰는 기존 방식(이하 IK 모드), 둘째는 노트북 CPU에서 처음부터 학습한 합성곱 신경망 정책(이하 CNN 정책), 셋째는 π0.5를 미세조정하여 원격 GPU에서 실행하는 정책(이하 π0.5 정책)이다. 두 정책은 같은 시연 장면으로 학습하고 같은 장면에서 평가하여 모델 차이만 드러나도록 하였다. 평가 항목은 집기 성공률, 소요 단계, 명령 문장의 활용 여부와 문장만으로 세 상자 중 하나를 고르는 능력, 시연에 없던 명령 문장과 조명, 재질, 방해물 같은 시각 변화에 대한 강인성, 전체 작업에서의 성공률과 시간, 계산 비용이다. 특히 사전 학습 모델에 기대되는 장점인 적은 학습량으로의 적응, 원격 실행에 따른 지연에 대한 강인성, 범용 구조와 언어 처리 능력이 이 작업에서 어떻게 나타나는지 살펴본다.'),
        (C, '2. 시스템 구성'),
        (S, '2.1 시뮬레이션 환경'),
        (B, '물리 시뮬레이션은 MuJoCo^{(10)} 3.12, 로봇 소프트웨어는 ROS 2^{(11)} Humble을 사용하였다. 로봇은 차동 구동 이동 플랫폼에 7자유도 팔 두 개(OpenArm)와 평행 그리퍼를 얹은 구조이며, 2차원 LiDAR, 머리 카메라(1280×720, 47° 하향), 손목 카메라를 갖는다. 작업 공간은 10 m × 8.5 m의 방이고, 높이 0.65 m의 공급 테이블 3개와 작업대 1개가 있다. 물체는 빨강, 초록, 파랑의 5 cm 정육면체 상자이며 윗면에 한 변 3.75 cm의 ArUco 마커가 붙어 있다. 테이블의 놓을 자리에는 한 변 7.5 cm의 마커가 있다.'),
        ('fig', ('fig_system.png', 80, 80, 'Fig. 1 Task pipeline shared by the three modes. Only the pick step differs')),
        (S, '2.2 공통 작업 절차'),
        (B, 'Fig. 1은 작업 절차를 나타낸다. 계획기가 명령을 이동, 집기, 놓기로 나누면, 로봇은 Nav2^{(12)}로 테이블 앞까지 주행한 뒤 ArUco 마커를 보며 상자를 팔이 닿기 좋은 위치에 맞춘다. 이 정렬은 목표 위치에서 1 cm 이내로 멈춘다. 그다음 집기를 수행하고, 0.35 m 후진한 뒤 목적지로 이동하여 MoveIt^{(1)}으로 놓는다. 세 방식은 집기 단계만 다르고 나머지는 같다. 따라서 VLA 정책을 쓰는 모드에서도 정렬과 놓기에는 마커가 쓰이며, 정책 자체만 마커 좌표를 입력받지 않는다.'),
        (C, '3. 집기 방식'),
        (S, '3.1 IK 모드'),
        (B, 'IK 모드는 마커 검출로 얻은 자세를 5회 평균하여 상자 중심과 방향을 구하고, 상자 면에 맞춘 파지 자세를 계산한다. 그리퍼는 15° 아래로 기울어 접근한다. 파지 자세에서 10 cm 뒤, 4 cm 위의 예비 자세까지 MoveIt의 표본 기반 계획기로 이동하고, 직선으로 접근한 뒤 그리퍼를 닫아 8 cm 들어 올린다. 팔이 예비 자세에 도달하지 못하면 접은 자세에서 한 번 다시 시도한다. 왼팔과 오른팔 중 상자에 가까운 팔을 쓴다.'),
        (S, '3.2 CNN 정책'),
        (B, 'CNN 정책은 Levine 등^{(5)}의 공간 소프트맥스와 Zhao 등^{(6)}의 행동 청크를 결합한 소형 모델이다. 머리 영상(128×72)과 손목 영상(96×96)은 각각 합성곱 3층과 공간 소프트맥스를 거쳐 특징점 64개의 좌표가 된다. 명령 문장의 단어는 해시로 임베딩하여 평균하고, 관절각과 함께 은닉층 2개의 다층 퍼셉트론에 넣는다. 출력은 앞으로 *{H} = 10 단계(1 s)의 관절 목표 8개씩과 종료 확률이다. 손실은 다음과 같다.'),
        ('eq', ('L = {1} over {H} sum from {k=0} to {H-1} LEFT | hat{a} _{t+k} - a _{t+k} RIGHT | _{1} + 0.1 L _{BCE} ( d _{t} )', 1)),
        (B, '여기서 행동은 정규화된 값이고 *{L}_{BCE}는 종료 여부의 이진 교차 엔트로피이다. 실행 시에는 10 Hz로 매 단계 추론하고, 겹치는 청크의 예측을 지수 가중 평균하여 관절 목표를 정한다.^{(6)} 매개변수는 597,329개이다.'),
        (S, '3.3 π0.5 정책'),
        (B, 'π0.5^{(9)}는 PaliGemma^{(15)} 기반의 영상-언어 인코더와 흐름 정합^{(16)}으로 행동을 생성하는 디코더로 구성된다. 잡음 ε와 행동 *{a}를 τ로 보간한 값을 *{x}_{τ}라 할 때, 디코더 *{v}_{θ}는 다음 손실로 학습한다.'),
        ('eq', ('L = E LEFT [ LEFT | v _{theta} ( x _{tau} , tau , I _{h} , I _{w} , l , s _{t} ) - ( epsilon - a ) RIGHT | ^{2} RIGHT ]', 2)),
        (B, '사전 학습 가중치에 LoRA^{(17)}를 적용하여 전체 34.03억 개의 매개변수 중 4.67억 개만 학습하였다. 입력은 머리 영상(위아래에 검은 띠를 붙인 224×224)과 손목 영상(224×224), 문장, 숫자 토큰으로 바꾼 관절각이다. 왼쪽 손목 입력은 가렸다. 출력에는 CNN 정책과 같은 종료 신호를 덧붙여 단계마다 9개 값으로 하였고, 팔 관절 7개는 청크 시작 상태에 대한 차이로 학습하였다. 실행 시에는 예측한 10 단계 중 5 단계를 수행하고 다시 추론한다. 노트북에 GPU가 없으므로 정책은 Google Colab에서 실행하고 웹소켓 터널로 연결하였다. 답을 기다리는 동안 팔은 마지막 목표에 멈춰 있어, 모델이 본 자세와 실제 자세가 어긋나지 않는다.'),
        (B, 'π0.5 정책은 구조상 CNN 정책과 다음 점에서 다르다. 첫째, 영상 입력의 화소 수가 CNN 정책보다 머리 영상은 약 3.1배(띠를 뺀 224×126), 손목 영상은 약 5.4배 많아 상자와 그리퍼의 세부를 더 많이 본다. 둘째, CNN 정책은 단어를 해시로 나눈 뒤 평균하므로 어순을 버리고 시연에 없던 단어는 거의 학습되지 않은 값으로 바뀌지만, π0.5는 사전 학습된 언어 모델의 토크나이저로 임의의 문장을 처리한다. 셋째, CNN 정책은 L1 회귀로 평균적인 행동 하나를 예측하는 반면, 흐름 정합은 행동의 분포에서 표본을 생성하므로 여러 해가 가능한 동작을 평균으로 뭉개지 않는다.^{(16)} 넷째, CNN 정책의 해상도, 특징점 수, 단어 처리 방식은 이 작업에 맞춰 정한 것이지만, π0.5는 같은 구조와 사전 학습 가중치를 그대로 쓰고 시연만 바꾸어 다른 작업에 적용할 수 있다. Table 1은 세 방식의 사양을 요약한 것이다.'),
        ('table', ('Table 1 Specifications of the three pick methods', [15, 17, 22, 22], [
            ['Item', 'IK mode', 'CNN policy', 'π0.5 policy'],
            ['Input', 'Marker pose', 'Images 128×72, 96×96; text; joints', 'Images 224×224 (two); text; joints'],
            ['Output', 'Motion plan', '10×8 targets, done', '10×9 (targets, done)'],
            ['Parameters', '-', '5.97×10^{5}', '3.40×10^{9} (4.67×10^{8} trained)'],
            ['Training', 'None', '20,000 steps × 64, CPU', '5,000 steps × 32, GPU'],
            ['Samples', '-', '1.28×10^{6} (14.4 epochs)', '1.60×10^{5} (1.8 epochs)'],
            ['Runs on', 'Laptop CPU', 'Laptop CPU', 'Remote GPU'],
            ['Arm', 'Either', 'Right', 'Right'],
        ])),
        (C, '4. 실험 방법'),
        (S, '4.1 시연 데이터'),
        (B, '두 정책은 같은 스크립트 전문가의 시연으로 학습하였다. 전문가는 시뮬레이터가 아는 상자의 실제 자세로 감쇠 최소제곱 IK^{(13)}를 풀어 3.1절과 같은 경유점을 따라간다.'),
        ('eq', ('DELTA q = J ^{T} ( J J ^{T} + lambda ^{2} I ) ^{-1} e', 3)),
        (B, '장면은 테이블 4개, 상자 3색, 놓을 자리를 무작위로 고르고, 상자 위치 ±3 cm, 상자 방향 ±45°, 로봇 정렬 오차 전후 ±4 cm, 좌우 ±5 cm, 방향 ±8°로 흩뜨렸다. 절반의 시연에는 옆자리에 다른 색 상자를 두었고, 절반에는 실행 목표에 서서히 변하는 잡음을 더하였다.^{(14)} 명령 문장은 7개 문형과 색 3가지로 만든 21종이다. 시도 1,200회 중 성공한 1,155개(88,935 프레임)를 사용하였고, 두 정책의 시연은 같은 난수 시드로 만들어 영상 해상도만 다르다. Fig. 2는 각 정책의 입력 영상이다.'),
        ('fig', ('fig_views.png', 80, None, 'Fig. 2 Policy inputs for the same scene: head and wrist views of the CNN policy (top) and the π0.5 policy (bottom)')),
        (B, 'CNN 정책은 AdamW(학습률 10^{-3}, 배치 64)로 20,000 단계 학습하였다. π0.5 정책은 15,000 단계로 계획하였으나 본 논문에서는 5,000 단계 체크포인트(배치 32)를 사용하였다. CNN 정책의 영상 증강은 ±4 화소의 이동과 ±10%의 밝기, 대비 변화이고, π0.5 정책은 openpi의 기본 증강을 쓴다. 이 차이의 영향을 나누기 위해 CNN 정책을 openpi와 같은 증강으로 한 번 더 학습하였다(CNN-A). 머리 영상은 95% 크기로 무작위로 잘라 원래 크기로 늘리고 ±5° 회전하였으며, 두 영상 모두 절반의 확률로 밝기 ±0.3, 대비 ±0.4, 색상 ±0.1을 바꾸었다. openpi는 채도 0.5도 지정하지만 사용하는 augmax 구현에서는 채도 변화가 적용되지 않으므로 CNN-A에도 넣지 않았다. 나머지 설정과 난수 시드는 CNN 정책과 같고, 검증 L1 오차는 0.0377로 CNN 정책의 0.0385와 비슷하였다.'),
        (B, '정책이 문장만으로 물체를 고르는지 보기 위해 고르기 과제를 따로 만들었다. 빨강, 초록, 파랑 상자를 오른팔 앞에 10 cm 간격으로 한 줄로 놓고, 로봇은 특정 상자가 아니라 가운데 자리에 맞춰 선다. 가운데 상자는 로봇 기준 *{y} = -0.08 m에 있고, 정렬 오차는 좌우 ±2.5 cm, 자리별 위치 흩어짐은 ±1.5 cm, 상자 방향은 ±20°이다. 손가락이 이웃 상자에 닿지 않도록 이 과제에서는 그리퍼를 덜 벌렸다. Fig. 3은 이 과제의 첫 시험 장면에서 π0.5 정책이 받는 영상이다.'),
        ('fig', ('fig_row.png', 80, None, 'Fig. 3 Policy inputs for the first scene of the choosing task (π0.5 resolution): three boxes in a row, the robot lined up on the middle slot, and the instruction "pick up the red box" naming the left box')),
        (B, '명령은 기존 7개 문형의 색 명령이거나, "pick up the box on the left"와 같은 5개 문형의 위치 명령이다. 조합 일반화를 보기 위해 빨간 상자가 오른쪽 자리에 있을 때의 색 명령과 "in the middle"이라는 위치 명령은 시연에서 뺐다. 시도 2,000회 중 성공한 1,659개(127,743 프레임)를 사용하였으며, 이 중 945개가 색 명령이고 모두 집은 상자의 색을 말한다. CNN 정책은 앞과 같은 구조와 설정으로 다시 학습하였다. 또한 단어 해시 평균이 원인인지 보기 위해, 문장 인코더를 사전 학습된 문장 임베딩 모델 MiniLM^{(19,20)}으로 바꾼 정책(이하 CNN+MiniLM)도 학습하였다. 이 정책은 고정된 all-MiniLM-L6-v2 모델이 내는 384차원 임베딩을 선형층으로 줄여 쓴다. 검증 L1 오차는 CNN 정책이 0.0409, CNN+MiniLM 정책이 0.0403이었다. π0.5 정책도 같은 시연으로 집기 과제와 같은 설정에서 5,000 단계 학습하였으나, GPU 메모리 때문에 배치 크기는 16으로 줄였다. 따라서 학습 중에 본 표본은 80,000개(약 0.6 에폭)로 집기 과제의 절반이다.'),
        (S, '4.2 평가 방법'),
        (B, '폐루프 집기 시험은 ROS 없이 MuJoCo 장면에서 수행하였다. 학습에 쓰지 않은 난수 시드로 만든 100개 장면에서 정책을 실행하고, 상자가 3 cm 이상 들리면 성공으로 판정하였다. 최대 길이는 120 단계이고, 종료 확률이 3 단계 연속 0.5를 넘으면 끝낸다. 같은 장면에서 전문가도 실행하여 기준으로 삼았다. 이 시험의 정렬 오차는 4.1절의 범위로, 실제 정렬 정밀도보다 넓다.'),
        (B, '언어 활용 시험은 두 상자가 있는 20개 장면에서 정렬되지 않은 옆 상자의 색을 명령하고 어느 상자를 들었는지 기록하였다. 같은 장면에서 전문가에게 명령한 상자를 집게 하여, 그 상자가 팔이 닿는 위치에 있는지도 확인하였다. 명령 문장 강인성 시험은 폐루프 시험의 처음 50개 장면에서, 집을 상자의 색은 그대로 두고 문장만 바꾸어 성공률을 비교하였다. 문장은 시연 문형 그대로인 문장, 시연에 없던 단어로 된 영어 문장, 시연 문형에 관계없는 말을 덧붙인 문장, 한국어 문장의 네 종류이다(Table 3). π0.5 정책은 이 시험에서도 Colab의 서버를 터널로 호출하였고, 응답을 기다리는 동안 시뮬레이션을 멈추었다.'),
        (B, f'고르기 시험은 학습에 쓰지 않은 난수 시드로 만든 장면에서 여섯 조건을 50회씩 수행하였다(Table 4). 상자의 순서, 집을 자리, 문장은 조건과 장면 번호로 정하여 세 정책이 같은 장면과 문장을 받는다. L1은 시연에 있던 색-자리 조합의 색 명령, L2는 시연에서 뺀 빨강-오른쪽 조합의 색 명령, L3은 시연에 있던 왼쪽, 오른쪽 위치 명령, L4는 시연에서 뺀 "in the middle" 명령이다. L5는 L1과 같은 조합을 짝수 장면에서는 "could you please fetch me that red block"처럼 시연에 없던 영어 표현으로, 홀수 장면에서는 "빨간 상자를 집어 줘"처럼 한국어로 명령하였다. L6은 "pick up the box to the left of the green box"처럼 이웃 상자로 목표를 가리키는 형식으로, 시연에 없던 문장 구조이다. 명령한 자리의 상자만 약 3 cm 이상 들리면 성공으로 하였고, 두 상자를 함께 들면 실패로 하였다. 같은 장면에서 전문가는 조건별로 {min(int(m[f"row_expert_L{i}"].split("/")[0]) for i in range(1, 7))}~{max(int(m[f"row_expert_L{i}"].split("/")[0]) for i in range(1, 7))}회 성공하였다.'),
        (B, '시각 변화 시험은 같은 50개 장면에서 정책은 그대로 두고 장면의 모습만 한 가지씩 바꾸었다(Table 5, Fig. 5). 조건과 수치는 결과를 보기 전에 정하였다. 조명은 머리 위 방향광과 헤드라이트의 밝기를 0.4배로 줄이거나(V1), 따뜻한 색으로 바꾸거나(V2), 방향광을 수평에 가깝게 기울였다(V3). V4는 테이블 상판을 진한 갈색으로 바꾸었고, V5는 바닥의 회색 체크 무늬를 녹색으로 물들이고 4배 촘촘하게 하였다. V6은 학습에 없던 은색 캔(지름 6.6 cm)과 주황 공(지름 7 cm)을 상자에서 약 13 cm 떨어진 곳에 고정하였고, V7은 집을 상자를 노랑으로 바꾸고 "pick up the yellow box"로 명령하였다. V8은 머리 카메라를 아래로 3° 더 기울였다. 전문가는 V0과 V6에서 모두 성공하여, 방해물이 집기 동작을 막지 않음을 확인하였다.'),
        (B, '전체 스택 시험은 ROS 환경에서 세 상자를 작업대에 모은 뒤 제자리로 되돌리는 작업을 3회 반복하여 집기 18회를 수행하는 것을 한 세트로 하였다. IK 모드는 2세트(36회), CNN 정책과 π0.5 정책은 각각 1세트(18회)를 수행하였다. π0.5 정책은 Colab의 A100에서 서버로 실행하고 cloudflared 터널로 노트북의 ROS 노드와 연결하였다. 작업 계획은 고정된 스크립트를 사용하여 언어 모델의 영향을 배제하였고, 회차마다 환경을 초기화하였다. 앞선 실패 때문에 수행할 수 없게 된 동작은 집계에서 제외하였다.'),
        (B, '계산 환경은 노트북(Intel Core Ultra 7 258V, 8코어, 외장 GPU 없음, WSL2 Ubuntu 22.04)과 Google Colab의 NVIDIA A100이다. 집기 과제에서 π0.5 정책의 학습, 폐루프 평가, 전체 스택 시험의 추론은 모두 A100에서 수행하였다. 고르기 과제의 π0.5 정책은 Colab의 NVIDIA L4(24 GB)에서 학습하였다.'),
        (C, '5. 결과 및 고찰'),
        (S, '5.1 폐루프 집기 성능'),
        (B, f'Table 2와 같이 두 정책과 전문가 모두 100개 장면에서 전부 성공하였다. 두 상자가 있던 43개 장면에서도 다른 상자를 든 경우는 없었다. 집기에 걸린 단계는 CNN 정책이 평균 75.0 (표준편차 2.1), π0.5 정책이 77.5 (표준편차 5.1)로, 같은 장면끼리 짝지은 Wilcoxon 부호 순위 검정에서 차이가 유의하였다(*{{p}} < 0.001). Fig. 4의 분포를 보면 CNN 정책은 전문가의 77 단계 부근에 좁게 모이고, π0.5 정책은 67~90 단계로 넓게 퍼진다. 표본 기반 생성과 5 단계 개루프 실행이 원인일 수 있으나 본 실험만으로 구분할 수는 없다. 증강을 바꾼 CNN-A 정책은 {m["aug_rate"]} 성공하여, 1회는 120 단계 안에 상자를 들지 못하였다. 성공한 집기의 단계는 평균 {m["aug_steps"].replace(" ± ", " (표준편차 ")})였다.'),
        ('table', ('Table 2 Closed-loop results on the same test scenes. CNN-A: CNN retrained with the augmentation of π0.5', [12, 14, 22, 26], [
            ['Method', 'Success', 'Steps (mean ± SD)', 'Other box asked: named / lined-up'],
            ['Expert', '100/100', '77 (fixed plan)', '-'],
            ['CNN', '100/100', '75.0 ± 2.1', '0/20, 20/20'],
            ['CNN-A', m['aug_rate'], m['aug_steps'], m['aug_other']],
            ['π0.5', '100/100', '77.5 ± 5.1', '0/20, 20/20'],
        ])),
        ('fig', ('fig_steps.png', 80, 63.5, 'Fig. 4 Steps per pick on the 100 test scenes. The dashed line is the expert plan')),
        (S, '5.2 명령 문장의 활용'),
        (B, '옆 상자의 색을 명령한 20개 장면에서 두 정책 모두 명령한 상자를 한 번도 집지 않았고 20회 모두 정렬된 상자를 집었다(Table 2). 다만 옆 상자는 25~30 cm 떨어져 있어, 전문가가 같은 자세에서 명령한 상자를 들 수 있었던 장면은 9개였다. 오른팔이 닿는 이 9개 장면에서도 두 정책은 모두 정렬된 상자를 집었다. 시연에서는 정렬된 상자가 언제나 명령한 상자이므로, 색 낱말을 읽지 않아도 손실을 줄일 수 있다. 이는 지름길 학습^{(18)}의 사례이다. 사전 학습된 언어 인코더를 가진 π0.5도 같은 결과를 보인 것은, 이 데이터에서는 모델의 언어 능력보다 데이터의 구성이 결과를 좌우함을 시사한다. 작업 전체에서는 계획기가 명령한 상자의 마커로 먼저 정렬하므로 이 약점이 드러나지 않지만, 마커 없이 언어로 물체를 고르려면 정렬되지 않은 상자를 집는 시연이 필요하며, 5.3절에서 이를 시험하였다.'),
        (B, f'반면 문장의 형태가 시연과 다를 때는 두 정책의 차이가 뚜렷하였다(Table 3). 시연에 없던 단어로 명령하면 CNN 정책은 {m["para_cnn_unseen_words"]}, 한국어로 명령하면 {m["para_cnn_korean"]}으로 120 단계 동안 상자를 들지 못하였으나, π0.5 정책은 각각 {m["para_pi05_unseen_words"]}, {m["para_pi05_korean"]} 성공하였다(Fisher 정확 검정, 두 경우 모두 *{{p}} {m["para_p_korean"]}). 관계없는 말을 덧붙인 문장에서는 CNN 정책도 {m["para_cnn_distracting"]}로 대부분 성공하였고 π0.5 정책은 {m["para_pi05_distracting"]}였다(*{{p}} {m["para_p_distracting"]}). 이 차이는 3.3절의 단어 처리 방식으로 설명할 수 있다. CNN 정책은 시연의 단어가 남아 있으면 평균 임베딩이 학습 범위에 머물지만, 낯선 단어만 있으면 학습되지 않은 값이 되고, 한글은 영문 단어만 읽는 토크나이저에서 빈 문장이 된다. 이렇게 학습 범위 밖의 입력이 들어가면 집기를 끝내지 못한 것으로 보인다. π0.5는 사전 학습된 언어 모델이 낯선 표현과 다른 언어도 학습한 문장과 가까운 표현으로 바꾸어, 동작이 흔들리지 않은 것으로 해석된다.'),
        (B, '다만 앞의 시험에서 두 정책 모두 색 낱말을 읽지 않았으므로, π0.5의 이점은 문장의 뜻을 이해하는 능력이라기보다 낯선 문장에도 학습한 동작을 유지하는 강인성이다. 사람이 명령하는 실제 환경에서는 표현이 시연과 같을 수 없으므로 이 강인성은 실용상 중요하며, 별도의 문장 증강 없이 사전 학습만으로 얻어졌다는 점에서 의미가 있다.'),
        ('table', ('Table 3 Closed-loop pick success with instructions not used in the demonstrations (same 50 scenes)', [17, 35, 12, 12], [
            ['Instruction', 'Example', 'CNN', 'π0.5'],
            ['Seen template', 'pick up the red box', m['para_cnn_seen'], m['para_pi05_seen']],
            ['Unseen words', 'could you please fetch me that red block', m['para_cnn_unseen_words'], m['para_pi05_unseen_words']],
            ['Extra words', 'the weather is lovely today …, red box, pick it up for me', m['para_cnn_distracting'], m['para_pi05_distracting']],
            ['Korean', '빨간 상자를 집어 줘', m['para_cnn_korean'], m['para_pi05_korean']],
        ])),
        (S, '5.3 문장으로 상자 고르기'),
        (B, f'Table 4는 고르기 시험의 결과이다. 시연에 있던 조합의 색 명령(L1)에서 π0.5 정책은 {m["row_pi05_L1"]} 성공하였으나 CNN 정책은 {m["row_cnn_L1"]}, CNN+MiniLM 정책은 {m["row_minilm_L1"]}이었다(Fisher 정확 검정, 각각 *{{p}} {m["row_p_cnn_L1"]}). 목표 자리별로 보면 CNN 정책은 가운데 상자를 명령하면 {m["row_cnn_L1_middle"]}, 왼쪽은 {m["row_cnn_L1_left"]} 성공하였으나 오른쪽 상자는 {m["row_cnn_L1_right"]}로 한 번도 집지 못하였고, 실패는 대부분 다른 상자를 든 경우였다(CNN {m["row_cnn_L1_wrong"]}회, CNN+MiniLM {m["row_minilm_L1_wrong"]}회). π0.5 정책은 왼쪽 {m["row_pi05_L1_left"]}, 가운데 {m["row_pi05_L1_middle"]}, 오른쪽 {m["row_pi05_L1_right"]}로 자리에 관계없이 성공하였고 다른 상자를 든 경우는 {m["row_pi05_L1_wrong"]}회였다. 시연에서 뺀 빨강-오른쪽 조합(L2)에서는 차이가 더 커서, π0.5 정책은 {m["row_pi05_L2"]} 성공하였고 두 CNN 정책은 한 번도 성공하지 못하였다. 세 정책이 같은 시연으로 학습하였으므로 이 차이는 모델에서 온 것이다. π0.5 정책은 색 낱말을 영상 속 상자와 연결하였고, 색과 자리를 따로 본 시연에서 처음 보는 조합으로 일반화한 반면, CNN 계열은 색 명령을 사실상 무시하였다.'),
        (B, f'위치 명령에서는 결과가 달랐다. 시연에 있던 왼쪽, 오른쪽 명령(L3)에서는 CNN 정책 {m["row_cnn_L3"]}, CNN+MiniLM 정책 {m["row_minilm_L3"]}로 π0.5 정책의 {m["row_pi05_L3"]}보다 오히려 높았다(*{{p}} = {m["row_p_cnn_L3"]}, {m["row_p_minilm_L3"]}). 시연에서 뺀 "in the middle"(L4)은 두 CNN 정책 모두 한 번도 성공하지 못하였고, 각각 {m["row_cnn_L4_lifted"]["left"]}회, {m["row_minilm_L4_lifted"]["left"]}회 왼쪽 상자를 집었다. π0.5 정책은 {m["row_pi05_L4"]} 성공하였으나 왼쪽 {m["row_pi05_L4_lifted"]["left"]}회, 가운데 {m["row_pi05_L4_lifted"]["middle"]}회, 오른쪽 {m["row_pi05_L4_lifted"]["right"]}회를 들고 {m["row_pi05_L4_lifted"]["none"]}회는 들지 못하여, 세 상자 중 하나를 무작위로 고르는 수준과 구별되지 않았다(이항 검정, *{{p}} = {m["row_p_chance_L4"]}).'),
        (B, f'시연에 없던 영어 표현(L5의 짝수 장면)에서는 π0.5 정책이 {m["row_pi05_L5_en"]} 성공하였고, CNN 정책은 {m["row_cnn_L5_en"]}, CNN+MiniLM 정책은 {m["row_minilm_L5_en"]}였다. 반면 한국어 명령(홀수 장면)에서는 π0.5 정책도 {m["row_pi05_L5_ko"]}에 그쳤다. 5.2절에서 π0.5 정책은 한국어 명령으로 50회 모두 성공하였으나, 그때는 정렬된 상자를 집으면 되었으므로 색 낱말을 이해할 필요가 없었다. 영어 시연만으로 학습한 색 낱말이 한국어 색 낱말로는 이어지지 않은 것으로, 5.2절의 한국어 결과는 뜻의 이해가 아니라 동작의 유지로 해석해야 함을 확인시켜 준다. 영어 전용인 MiniLM을 쓴 정책은 한국어 명령에서 {m["row_minilm_L5_ko"]}였다.'),
        (B, f'이웃 상자로 목표를 가리킨 L6에서는 세 정책 모두 문장 구조를 따르지 못하였다. CNN 정책은 {m["row_cnn_L6"]}, CNN+MiniLM 정책은 {m["row_minilm_L6"]} 성공하였으나, 목표가 가운데 상자인 장면에서는 각각 {m["row_cnn_L6_middle"]}, {m["row_minilm_L6_middle"]}로 모두 실패하고 목표가 양 끝인 장면에서만 성공하였다. 문장 속의 "left", "right"를 L3의 위치 명령처럼 받아들여 그쪽 끝의 상자를 집었고, 목표가 마침 그 끝에 있을 때만 맞은 것이다. π0.5 정책은 {m["row_pi05_L6"]}로 CNN 정책과 유의한 차이가 없었고(*{{p}} = {m["row_p_cnn_L6"]}), 가운데 목표에서도 {m["row_pi05_L6_middle"]}에 그쳤다.'),
        (B, '정리하면, 같은 시연으로 학습하였을 때 색 낱말을 영상 속 상자와 연결하고 시연에 없던 색-자리 조합으로 일반화한 것은 π0.5 정책뿐이었다. 그것도 CNN 정책이 본 표본의 16분의 1(80,000개, 약 0.6 에폭)만 보고 얻은 결과이다. 문장 인코더만 사전 학습된 MiniLM으로 바꾼 CNN+MiniLM 정책은 이 능력을 얻지 못하였으므로, 이 과제에서는 문장 인코더의 사전 학습만으로는 부족하고 영상과 언어를 함께 사전 학습한 모델이 유리하였다. 반면 시연에 없던 위치 낱말, 한국어 색 낱말, 관계 문장처럼 시연의 문형에서 더 멀어지면 π0.5 정책도 명령을 따르지 못하였다.'),
        ('table', ('Table 4 Closed-loop success in choosing one of three boxes by the instruction (50 scenes each). L5: 25 scenes of unseen English wording and 25 of Korean. *: colour-slot combination or position word held out of the demonstrations. MiniLM: CNN with a frozen MiniLM sentence encoder', [23, 11, 11, 12, 11], [
            ['Test', 'Expert', 'CNN', 'MiniLM', 'π0.5'],
            ['L1 Colour', m['row_expert_L1'], m['row_cnn_L1'], m['row_minilm_L1'], m['row_pi05_L1']],
            ['L2 Colour^{*}', m['row_expert_L2'], m['row_cnn_L2'], m['row_minilm_L2'], m['row_pi05_L2']],
            ['L3 Left / right', m['row_expert_L3'], m['row_cnn_L3'], m['row_minilm_L3'], m['row_pi05_L3']],
            ['L4 Middle^{*}', m['row_expert_L4'], m['row_cnn_L4'], m['row_minilm_L4'], m['row_pi05_L4']],
            ['L5 English', m['row_expert_L5_en'], m['row_cnn_L5_en'], m['row_minilm_L5_en'], m['row_pi05_L5_en']],
            ['L5 Korean', m['row_expert_L5_ko'], m['row_cnn_L5_ko'], m['row_minilm_L5_ko'], m['row_pi05_L5_ko']],
            ['L6 Relation', m['row_expert_L6'], m['row_cnn_L6'], m['row_minilm_L6'], m['row_pi05_L6']],
            ['Total', m['row_expert_all'], m['row_cnn_all'], m['row_minilm_all'], m['row_pi05_all']],
        ])),
        (S, '5.4 시각 변화에 대한 강인성'),
        (B, f'Table 5는 시각 변화 시험의 결과이다. 변화가 없는 V0에서는 두 정책 모두 50개 장면에서 전부 성공하였다. 장면을 바꾼 8개 조건을 합하면 CNN 정책은 {m["vis_cnn_all"]}({m["vis_cnn_pct"]}%), π0.5 정책은 {m["vis_pi05_all"]}({m["vis_pi05_pct"]}%) 성공하였다(Fisher 정확 검정, *{{p}} {m["vis_p_all"]}). CNN 정책은 옆에서 비추는 조명(V3)에서 {m["vis_cnn_V3"]}, 갈색 상판(V4)에서 {m["vis_cnn_V4"]}, 어두운 조명(V1)에서 {m["vis_cnn_V1"]}로 떨어졌고, π0.5 정책은 세 조건 모두 {m["vis_pi05_V3"]}이었다(각각 *{{p}} {m["vis_p_V3"]}). V3과 V4에서 CNN 정책이 실패한 70회 중 64회는 120 단계 동안 상자를 들지 못한 경우였다. 처음 보는 캔과 공을 둔 V6에서는 CNN 정책 {m["vis_cnn_V6"]}, π0.5 정책 {m["vis_pi05_V6"]}로 차이가 유의하지 않았다(*{{p}} = {m["vis_p_V6"]}). 따뜻한 조명(V2), 바닥 무늬(V5), 노랑 상자(V7), 카메라 기울기(V8)에서는 두 정책 모두 49회 이상 성공하였다. π0.5 정책의 유일한 실패는 V2의 한 장면으로, 120 단계 안에 상자를 들지 못하였다. 다른 상자를 든 경우는 두 정책 모두 없었다.'),
        (B, 'CNN 정책이 크게 떨어진 V3과 V4는 상자 주변의 테이블 밝기와 색, 그림자가 바뀌는 조건이다. CNN 정책의 공간 소프트맥스는 특징 지도에서 반응이 큰 지점의 좌표만 특징으로 쓰므로, 상자와 상판의 대비가 바뀌면 특징점의 위치가 학습 때와 달라져 동작이 어긋난 것으로 보인다. 테이블 밖의 바닥만 바꾼 V5에서는 영향이 없었다. π0.5 정책은 대규모 영상으로 사전 학습된 시각 인코더와 높은 해상도를 써서 이런 변화에도 같은 특징을 얻은 것으로 해석된다. V7에서 두 정책이 모두 성공한 것은, 집기 과제로 학습한 정책이 5.2절과 같이 색 낱말을 읽지 않고 정렬된 상자를 집기 때문으로 보이며, 처음 보는 색을 이해하였다는 뜻은 아니다.'),
        ('table', ('Table 5 Closed-loop pick success under visual changes not seen in training (50 scenes each). CNN-A: CNN retrained with the augmentation of π0.5. p: Fisher exact test, CNN-A vs π0.5', [20, 11, 12, 11, 14], [
            ['Condition', 'CNN', 'CNN-A', 'π0.5', 'p'],
            ['V0 None', m['vis_cnn_V0'], m['vis_cnn_aug_V0'], m['vis_pi05_V0'], m['vis_pa_V0']],
            ['V1 Dim', m['vis_cnn_V1'], m['vis_cnn_aug_V1'], m['vis_pi05_V1'], m['vis_pa_V1']],
            ['V2 Warm', m['vis_cnn_V2'], m['vis_cnn_aug_V2'], m['vis_pi05_V2'], m['vis_pa_V2']],
            ['V3 Side', m['vis_cnn_V3'], m['vis_cnn_aug_V3'], m['vis_pi05_V3'], m['vis_pa_V3']],
            ['V4 Table', m['vis_cnn_V4'], m['vis_cnn_aug_V4'], m['vis_pi05_V4'], m['vis_pa_V4']],
            ['V5 Floor', m['vis_cnn_V5'], m['vis_cnn_aug_V5'], m['vis_pi05_V5'], m['vis_pa_V5']],
            ['V6 Objects', m['vis_cnn_V6'], m['vis_cnn_aug_V6'], m['vis_pi05_V6'], m['vis_pa_V6']],
            ['V7 Yellow', m['vis_cnn_V7'], m['vis_cnn_aug_V7'], m['vis_pi05_V7'], m['vis_pa_V7']],
            ['V8 Tilt', m['vis_cnn_V8'], m['vis_cnn_aug_V8'], m['vis_pi05_V8'], m['vis_pa_V8']],
            ['V1–V8', m['vis_cnn_all'], m['vis_cnn_aug_all'], m['vis_pi05_all'], m['vis_pa_all']],
        ])),
        (B, f'두 정책은 학습 때의 영상 증강도 다르므로, 4.1절의 CNN-A 정책으로 증강의 영향을 확인하였다. CNN-A 정책은 V0에서 {m["vis_cnn_aug_V0"]}, 8개 조건 합계 {m["vis_cnn_aug_all"]}({m["vis_cnn_aug_pct"]}%)로, 원래 CNN 정책의 {m["vis_cnn_all"]}보다 오히려 낮았고(*{{p}} {m["vis_pc_all"]}) π0.5 정책과의 차이도 유의하였다(*{{p}} {m["vis_pa_all"]}). 증강을 바꾸자 옆 조명(V3)은 {m["vis_cnn_V3"]}에서 {m["vis_cnn_aug_V3"]}로 나아졌으나(*{{p}} = {m["vis_pc_V3"]}), 어두운 조명(V1)은 {m["vis_cnn_V1"]}에서 {m["vis_cnn_aug_V1"]}, 따뜻한 조명(V2)은 {m["vis_cnn_V2"]}에서 {m["vis_cnn_aug_V2"]}, 캔과 공(V6)은 {m["vis_cnn_V6"]}에서 {m["vis_cnn_aug_V6"]}로 떨어졌고, 갈색 상판(V4)은 {m["vis_cnn_aug_V4"]}로 비슷하였다. V4를 뺀 조건에서 CNN-A 정책의 실패 124회 중 117회는 120 단계 동안 상자를 들지 못한 경우였고, V4에서는 실패 32회 중 21회가 상자를 들지 않은 채 종료를 판단한 경우였다. V1의 0.4배 밝기는 증강의 밝기 범위(최소 0.7배) 밖이고, V2처럼 색 채널마다 다르게 어두워지는 변화는 색상 회전과 밝기 변화로 만들어지지 않는다. 증강이 시험 조건을 덮지 못하면 넓은 증강이 오히려 해가 될 수 있는 것으로 보이나, 원인은 본 실험으로 확인하지 않았다. 따라서 π0.5 정책의 강인성은 영상 증강만으로는 설명되지 않으며, 사전 학습된 시각 인코더와 높은 해상도의 기여가 큰 것으로 판단된다. 다만 CNN-A는 한 번만 학습하였고, 작은 CNN에 맞추어 증강의 세기를 조정하지는 않았다.'),
        ('fig', ('fig_perturb.png', 80, None, 'Fig. 5 Head-camera view of the first test scene under each visual condition (π0.5 input without the black bands)')),
        (S, '5.5 전체 스택 성능'),
        (B, f'Table 6은 ROS 전체 스택의 결과이다. 집기 성공률은 IK 모드 {m["ik_rate_long"]}, CNN 정책 {m["cnn_rate_long"]}, π0.5 정책 {m["pi05_rate_long"]}이었으나, 표본이 작아 IK 모드와 각 정책의 차이는 통계적으로 유의하지 않았다(Fisher 정확 검정, *{{p}} = {m["fisher"]}, {m["fisher_pi05"]}). 정책의 단계 수는 평균 CNN {m["cnn_steps"]}, π0.5 {m["pi05_steps"]}로 폐루프 시험의 75.0, 77.5보다 약간 길었다.'),
        (B, f'IK 모드의 실패 {m["ik_fail"]}회는 모두 로봇이 작업대에 놓았던 상자를 다시 집는 되돌리기 단계에서 발생하였고, 공급 테이블의 초기 위치에서 집는 모으기 단계는 {m["ik_gather"]}회 모두 성공하였다. 원인 기록을 남긴 두 번째 세트의 실패 2회 중 1회는 앞선 놓기에서 접촉 때문에 상자가 목표보다 1.6 cm 위에서 풀린 경우로, 마커 높이가 평소보다 약 3 cm 높게 측정되었고 그리퍼가 빈손으로 닫혔다. 다른 1회는 예비 자세로 이동하던 팔의 관절 추종 오차(0.056 rad)가 허용치(0.02 rad)를 넘어 재시도까지 실패한 경우이다. 첫 번째 세트의 실패 3회는 원인 기록이 없다. 두 정책은 되돌리기에서도 실패하지 않았으나, 오른팔만 쓰므로 놓인 상자의 상태가 IK 모드와 달라 이를 정책의 강인성으로 단정할 수는 없다.'),
        (B, f'성공한 집기의 평균 시간은 IK 모드 {m["ik_time"]} s, CNN 정책 {m["cnn_time"]} s, π0.5 정책 {m["pi05_time"]} s였다. 이 시간에는 정렬, 집기, 후진, 팔 접기가 모두 포함된다. 다만 두 VLA 모드는 영상을 10 Hz로 렌더링하고 손목 카메라도 켜므로 시뮬레이션이 느려지는 것으로 보이며, 팔을 쓰지 않는 주행 시간도 IK 모드의 평균 {m["ik_nav"]} s에서 CNN {m["cnn_nav"]} s, π0.5 {m["pi05_nav"]} s로 늘었다. 따라서 IK 모드와 정책 사이의 벽시계 시간 차이를 방식 자체의 속도 차이로 해석할 수는 없다. 같은 렌더링 조건인 두 정책 사이에서는 π0.5 정책이 {m["pi05_minus_cnn"]} s 더 걸렸으며, 그 원인은 5.6절의 서버 응답 대기이다.'),
        ('table', ('Table 6 Results through the full ROS stack. Times are wall-clock means of successful actions', [9, 13, 17, 17, 12], [
            ['Mode', 'Pick success', 'Pick time (s)', 'Drive time (s)', 'Place success'],
            ['IK', m['ik_rate'], m['ik_time_sd'], m['ik_nav_sd'], m['ik_place']],
            ['CNN', m['cnn_rate'], m['cnn_time_sd'], m['cnn_nav_sd'], m['cnn_place']],
            ['π0.5', m['pi05_rate'], m['pi05_time_sd'], m['pi05_nav_sd'], m['pi05_place']],
        ])),
        (S, '5.6 계산 비용'),
        (B, f'CNN 정책은 노트북 CPU 8스레드로 5,272 s 동안 학습하였고, 추론은 4스레드로 호출당 평균 1.63 ms(200회)였다. 제어 주기 100 ms에 비해 충분히 짧다. π0.5 정책의 학습은 A100에서 초당 약 0.32 단계로, 5,000 단계에 약 4.4 시간이 걸렸고 GPU 메모리를 36.9 GB 사용하였다. 매개변수 수는 CNN 정책의 약 5,700배이다. 반면 학습 중에 본 표본 수는 CNN 정책이 1,280,000개(88,935 프레임의 약 14.4 에폭), π0.5 정책이 160,000개(약 1.8 에폭)로, π0.5 정책은 8분의 1의 표본으로 같은 100% 성공률에 도달하였다. 그것도 계획한 학습량의 3분의 1 시점이었다. 다만 CNN 정책이 더 이른 시점에 같은 성능에 이르는지는 확인하지 않았다. 폐루프 평가 100개 장면은 렌더링과 시뮬레이션을 포함해 406 s가 걸렸으므로, 추론 약 1,550회로 나누면 호출당 시간의 상한은 약 0.26 s이다. 전체 스택 시험에서 터널을 거친 왕복 시간은 {m["rtt_n"]}회 호출에서 중앙값 {m["rtt_median"]} s, 평균 {m["rtt_mean"]} s, 최대 {m["rtt_max"]} s였다. 팔은 응답을 기다리는 동안 마지막 목표를 유지하고, 집기 한 번에 약 {m["rtt_per_pick"]}회 호출하므로 대기 시간은 집기당 약 {m["rtt_wait"]} s이다. 이는 5.5절에서 π0.5 정책의 집기가 CNN 정책보다 길었던 {m["pi05_minus_cnn"]} s와 비슷하다. 응답이 제어 주기보다 길어 동작이 5 단계씩 끊어지지만, 이 작업에서는 성공률에 영향을 주지 않았다.'),
        (S, '5.7 고찰'),
        (B, f'π0.5 정책의 장점은 다섯 가지로 나타났다. 첫째, 시연에 없던 단어나 한국어로 명령해도 동작하였다. CNN 정책은 같은 조건에서 한 번도 성공하지 못하였다. 둘째, 세 상자 중 하나를 고르는 시연으로 학습하였을 때 색 낱말을 영상 속 상자와 연결하였고, 시연에서 뺀 색-자리 조합에서도 {m["row_pi05_L2"]} 성공하였다. 같은 시연으로 학습한 CNN 정책은 문장 인코더를 사전 학습된 MiniLM으로 바꾸어도 색을 무시하였다. 셋째, 조명의 방향과 밝기, 테이블 색이 학습 때와 달라도 성공률을 유지하였다. 같은 조건에서 CNN 정책의 성공률은 {100 * int(m["vis_cnn_V3"].split("/")[0]) // 50}~{100 * int(m["vis_cnn_V1"].split("/")[0]) // 50}%로 떨어졌다. π0.5와 같은 영상 증강으로 다시 학습한 CNN 정책도 8개 조건 합계 {m["vis_cnn_aug_pct"]}%에 그쳐, 이 강인성은 증강보다 사전 학습에서 온 것으로 보인다.'),
        (B, f'넷째, 사전 학습 가중치에서 출발하여 CNN 정책이 본 표본의 8분의 1, 계획한 학습량의 3분의 1만으로 폐루프 시험과 전체 스택 시험에서 모두 실패 없이 동작하였다. 시연 수집이 비싼 실제 로봇에서는 이 차이가 더 중요해진다. 다섯째, 추론을 원격 GPU에 맡겨 왕복 시간이 평균 {m["rtt_mean"]} s, 최대 {m["rtt_max"]} s로 제어 주기의 수 배에서 수십 배에 이르렀는데도 집기 18회가 모두 성공하였다. 행동 청크를 생성하는 구조 덕분에 추론이 제어 주기보다 느려도 동작할 수 있어, 로봇에 GPU를 싣지 않고 대형 모델을 쓸 수 있음을 보였다.'),
        (B, '반면 시연과 같은 문장을 쓰는 정상 조건에서는, 정렬 오차가 학습 범위 안에 있는 이 작업에서 성공률과 시간의 이득은 관찰되지 않았다. 100개 장면에서 두 정책이 모두 100%에 도달하여 성공률로는 구분되지 않으므로, 이 결과를 두 모델의 능력이 같다는 뜻으로 해석해서는 안 된다. 5.2~5.4절처럼 시연과 다른 문장이나 장면을 주거나 문장으로 물체를 골라야 할 때 차이가 드러났다. 시연에 있던 왼쪽, 오른쪽 위치 명령에서는 오히려 CNN 정책의 성공률이 높았고, 시연에 없던 위치 낱말, 한국어 색 낱말, 관계 문장은 π0.5 정책도 따르지 못하여, 사전 학습의 이점은 시연과 가까운 표현에서 주로 나타났다. 한편 마커가 가려지거나 없는 상황에서는 IK 모드가 불리할 것으로 예상되나 본 연구에서는 시험하지 않았다.'),
        (B, '본 연구의 한계는 다음과 같다. 첫째, 모든 결과는 시뮬레이션에서 얻었으며 실제 로봇으로 검증하지 않았다. 둘째, IK 모드는 ROS 스택에서만 시험하여 폐루프 시험의 두 정책과 직접 비교할 수 없다. 전문가는 실제 자세를 쓰므로 인식 오차가 없는 상한에 해당한다. 셋째, 두 정책의 학습 단계 수가 다르고, π0.5는 계획의 3분의 1만 학습하였다. 넷째, 전체 스택 시험의 표본이 IK 모드 36회, 두 정책 각 18회로 작아 성공률 차이를 판별하기 어렵다. 다섯째, VLA 모드도 정렬과 놓기에 마커를 쓰므로 마커 의존성을 없앤 것은 아니다. 여섯째, 명령 문장 강인성 시험은 문장 세 종류로 한정되었고 폐루프 시험에서만 수행하였다. 일곱째, 시각 변화 시험은 조건마다 한 가지 수준만 시험하였고, 증강을 맞춘 CNN-A 정책은 한 번만 학습하여 학습 난수에 따른 편차를 확인하지 않았다. 또한 두 정책은 영상 해상도와 구조도 달라, 남은 차이를 사전 학습만의 효과로 단정할 수는 없다. 여덟째, 고르기 시험은 폐루프에서만 수행하였고 각 정책을 한 번씩만 학습하였다. 전체 스택에서는 계획기가 명령한 상자의 마커로 먼저 정렬하므로 이 능력이 쓰이지 않는다.'),
        (C, '6. 결 론'),
        (B, f'이동 양팔 로봇의 상자 집기에서 IK 모드, CNN 정책, π0.5 정책을 같은 시뮬레이션에서 비교하였다. 결론은 다음과 같다.'),
        (B, f'(1) 처음 보는 100개 장면에서 두 정책의 집기 성공률은 모두 100%였고, 소요 단계는 CNN 정책이 75.0으로 π0.5 정책의 77.5보다 짧고 편차도 작았다. ROS 전체 스택의 집기 성공률은 IK 모드 {m["ik_rate"]}, CNN 정책 {m["cnn_rate"]}, π0.5 정책 {m["pi05_rate"]}이었고, IK 모드의 실패는 모두 로봇이 놓았던 상자를 다시 집는 단계에서 발생하였다.'),
        (B, f'(2) 시연에 없던 단어나 한국어로 명령하면 CNN 정책은 {m["para_cnn_unseen_words"]}, {m["para_cnn_korean"]}으로 동작하지 못하였으나 π0.5 정책은 {m["para_pi05_unseen_words"]}, {m["para_pi05_korean"]} 성공하였다. 다만 정렬된 상자만 집는 시연으로 학습하면 두 정책 모두 옆 상자의 색 명령을 따르지 못하였고, 세 상자 중 하나를 문장으로 고르는 시연으로 학습하자 π0.5 정책만 색 명령에서 {m["row_pi05_L1"]}, 시연에서 뺀 색-자리 조합에서 {m["row_pi05_L2"]} 성공하였다. CNN 정책은 각각 {m["row_cnn_L1"]}, {m["row_cnn_L2"]}에 그쳤고 문장 인코더를 MiniLM으로 바꾸어도 나아지지 않았다. 시연에서 뺀 위치 낱말, 한국어 색 명령, 관계 문장은 π0.5 정책도 따르지 못하였다.'),
        (B, f'(3) 조명의 방향과 밝기, 테이블 색을 바꾸면 CNN 정책의 성공률은 50회 중 {m["vis_cnn_V3"].split("/")[0]}~{m["vis_cnn_V1"].split("/")[0]}회로 떨어졌으나 π0.5 정책은 모두 성공하였고, 시각 변화 8개 조건 전체에서 π0.5 정책은 {m["vis_pi05_all"]}, CNN 정책은 {m["vis_cnn_all"]} 성공하였다. CNN 정책을 π0.5와 같은 영상 증강으로 다시 학습하면 {m["vis_cnn_aug_all"]}로 오히려 낮아져, 이 차이는 영상 증강만으로 설명되지 않는다.'),
        (B, f'(4) π0.5 정책은 CNN 정책이 본 학습 표본의 8분의 1로 같은 성공률에 이르렀고, 원격 서버의 응답을 기다리느라 집기 한 번에 약 {m["pi05_minus_cnn"]} s 더 걸렸는데도 전체 스택에서 실패하지 않아, 사전 학습 모델의 적응 효율과 원격 실행 가능성을 보였다. 반면 매개변수가 약 5,700배 많고 원격 GPU가 필요하며, 시연과 같은 문장을 쓰는 정상 조건의 성공률과 시간에서는 우위가 나타나지 않았다.'),
        (B, '후속 연구에서는 여러 학습 난수와 같은 해상도의 비교로 사전 학습의 효과를 더 분리하고, 마커가 가려진 조건에서 IK 모드를 포함한 세 방식을 비교하며, 고르기 과제를 전체 스택으로 넓히고 다국어 시연과 관계 문장 시연이 일반화에 주는 영향을 검증할 필요가 있다.'),
    ]
