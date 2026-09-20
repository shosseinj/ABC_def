# پروژه QSNN + TEMP-DRIFT — نسخه فازبندی‌شده

این پروژه برای پیاده‌سازی مرحله‌به‌مرحله‌ی **Quantum Spiking Neural Network (QSNN)**،
حمله‌ی **TEMP-DRIFT** و دفاع **QUANTUM-TEMP** طراحی شده است.

## هدف نهایی پروژه

```text
Iris / MNIST / SHD
      ↓
Spike representation
      ↓
Quantum temporal encoding
      ↓
QSNN classifier
      ↓
TEMP-DRIFT attack
      ↓
Quantum drift ↑
Classical spike drift ↓
      ↓
QUANTUM-TEMP defense
```

هر فاز:
- هدف دارد
- فایل پیاده‌سازی دارد
- فایل تست دارد
- نمونه‌ی ورودی و خروجی دارد
- معیار عبور به فاز بعدی دارد

---

## Phase 0 — Environment
هدف: آماده‌سازی Python و کتابخانه‌ها.

اجرا:
```bash
python scripts/check_environment.py
```

شرط موفقیت:
```text
NumPy, scikit-learn, PyTorch, PennyLane, pytest = OK
```

---

## Phase 1 — Iris loading + preprocessing
هدف: بارگذاری Iris و نرمال‌سازی چهار feature عددی.

ورودی نمونه:
```text
[5.1, 3.5, 1.4, 0.2]
```

خروجی:
```text
4 normalized features in [0,1]
```

تست:
```bash
pytest tests/test_phase01_iris.py -q
```

---

## Phase 2 — TTFS spike encoding
قاعده‌ی baseline:

```text
t_i = T × (1 - x_i)
```

feature بزرگ‌تر → spike زودتر.

نمونه:
```text
input  = [0.2, 0.5, 0.8, 1.0]
T      = 100
output = [80, 50, 20, 0]
```

تست:
```bash
pytest tests/test_phase02_ttfs.py -q
```

---

## Phase 3 — Quantum angle encoding

```text
tau_i   = t_i / T
theta_i = (pi/2) × tau_i
```

نمونه:
```text
t = [0,25,50,100]
theta = [0, pi/8, pi/4, pi/2]
```

تست:
```bash
pytest tests/test_phase03_quantum_encoding.py -q
```

---

## Phase 4 — Build 4-qubit QSNN

Baseline پیشنهادی:
- 4 qubits
- 4 variational layers
- trainable RY + RZ
- CNOT chain
- Pauli-Z measurement
- Linear(4→3) classifier

تعداد پارامتر trainable:
```text
4 layers × 4 qubits × 2 rotations = 32 quantum params
Linear head = 4×3 + 3 = 15 params
Total = 47 params
```

تست:
```bash
pytest tests/test_phase04_qsnn.py -q
```

---

## Phase 5 — Clean training
اجرا:
```bash
python scripts/train_iris.py
```

گیت سریع (گرادیان، تغییر وزن، و save/load checkpoint):
```bash
python phase_runner.py --phase 5
```

خروجی:
```text
checkpoints/iris_qsnn_best.pt
results/iris_training_history.csv
results/iris_clean_metrics.json
```

---

## Phase 6 — Clean evaluation
Metrics:
- Accuracy
- Macro Precision
- Macro Recall
- Macro F1

Sanity threshold پیشنهادی:
```text
Accuracy >= 0.85
```

این threshold برای SOTA نیست؛ فقط برای اطمینان از سالم بودن baseline است.

پس از اجرای training:
```bash
python phase_runner.py --phase 6
```

---

## Phase 7 — Depth ablation
مدل‌های:
```text
L = 2
L = 4
L = 6
```

هدف: انتخاب یک baseline متعادل و بررسی sensitivity نسبت به عمق مدار.

اجرا و گیت artifact:
```bash
python scripts/run_depth_ablation.py
python phase_runner.py --phase 7
```

---

## Phase 8 — Random timing jitter
Baseline ساده‌ی حمله:

```text
t'_i = clip(t_i + delta_i, 0, T)
delta_i ~ Uniform(-epsilon, epsilon)
```

بودجه‌ها:
```text
1%, 2%, 5%, 10% of T
```

تست:
```bash
pytest tests/test_phase08_random_jitter.py -q
```

---

## Phase 9 — Quantum drift metrics
Metrics:
- Trace Distance
- Fidelity
- 1 - Fidelity

تست:
```bash
pytest tests/test_phase09_quantum_metrics.py -q
```

---

## Phase 10 — Classical stealth metrics
Metrics:
- Spike-count difference
- Firing-rate difference
- ISI histogram total variation
- Delta_cls

هدف:
```text
Quantum drift = high
Classical drift = low
```

تست:
```bash
pytest tests/test_phase10_stealth.py -q
```

---

## Phase 11 — TEMP-DRIFT
هدف:

```text
maximize quantum drift
subject to:
||delta_t||_inf <= epsilon
Delta_cls <= tau
```

در این Starter یک optimizer مرجع و ساده وجود دارد تا pipeline تست شود.
برای نتایج مقاله باید بعداً نسخه‌ی gradient-based نهایی جایگزین شود.

تست:
```bash
pytest tests/test_phase11_temp_drift.py -q
```

---

## Phase 12 — Attack Success Rate
برای هر attack:
- Clean accuracy
- Attacked accuracy
- ASR
- Trace distance
- 1-Fidelity
- Delta_cls

در این پروژه ASR untargeted فقط روی نمونه‌هایی محاسبه می‌شود که مدل clean آن‌ها
را درست طبقه‌بندی کرده است. اجرا:
```bash
python scripts/evaluate_iris_attacks.py
python phase_runner.py --phase 12
```

---

## Phase 13 — Attack sweep
```text
epsilon = {1,2,5,10}%
tau     = {1,5,10}%
```

```bash
python scripts/run_attack_sweep.py
python phase_runner.py --phase 13
```

نتایج فعلی مربوط به optimizer مرجع randomized هستند و نتیجه نهایی مقاله نیستند.

---

## Phase 14 — Attack baselines
مقایسه:
```text
Random jitter
Classical timing attack
TEMP-DRIFT
```

پیاده‌سازی فعلی:
- `Random Jitter`: بدون objective
- `Classical Timing`: PGD untargeted روی cross-entropy مدل frozen، 20 iteration، شروع صفر، projection روی بودجه‌ی زمان
- `TEMP-DRIFT Reference`: جستجوی randomized قدیمی و غیرنهایی

```bash
python scripts/run_phase14_comparison.py
python phase_runner.py --phase 14
```

## Phase 14.5 — Gradient TEMP-DRIFT

نسخه‌ی differentiable مقدار `1 - Fidelity` حالت product چهار qubit را maximize می‌کند.
برای پایداری از random start، 40 iteration، 3 restart و projected sign-gradient استفاده می‌شود.
در زمان optimization از surrogate تغییر ISI مرتب‌شده استفاده می‌شود، اما candidate نهایی فقط در
صورت عبور از معیار دقیق `classical_mismatch` و شرط `Delta_cls <= tau` پذیرفته می‌شود.
نقطه‌ی clean همیشه fallback feasible است. این نسخه classification loss را optimize نمی‌کند.

```bash
python scripts/run_gradient_attack_comparison.py
python phase_runner.py --phase 14.5
```

خروجی جدید فایل‌های قبلی reference را overwrite نمی‌کند:
```text
results/iris_attack_comparison_phase14.csv
results/iris_attack_comparison_phase14.json
results/iris_attack_comparison_gradient.csv
results/iris_attack_comparison_gradient.json
```

---

## Phase 15 — QUANTUM-TEMP
دفاع مبتنی بر:
```text
X/Y/Z measurements
→ Bloch estimation
→ clean reference
→ coherence drift score
```

پیاده‌سازی training-time مرحله‌ای:

```text
QT-Q:  CE(clean) + 0.1 * (1 - measured-feature fidelity)
QT-QP: CE(clean) + 0.1 * (1 - measured-feature fidelity) + 0.1 * symmetric KL
```

نویز training از `Uniform(-0.02T,+0.02T)` تولید و به `[0,T]` clamp می‌شود.
Fidelity کامل input-state نمی‌تواند weightهای مدل را regularize کند، چون unitary مشترک
fidelity را حفظ می‌کند. بنابراین این فاز fidelity توزیع measurementهای Z مدار را regularize
می‌کند. معماری و 47 پارامتر مدل تغییر نکرده‌اند.

```bash
python scripts/run_quantum_temp_phase15.py
python phase_runner.py --phase 15
```

نتیجه‌ی اولیه با lambdaهای 0.1 منفی است: clean accuracy ثابت ماند، اما ASR و drift گزارش‌شده
بهبود نکردند. معیار ISI هشت-bin همچنان فقط diagnostic محدود است و اثبات stealth نیست.

### Phase 15.1 — Ablation قدرت regularization

انتخاب فقط با validation انجام شد. Grid اول `lambda_q=5` و grid دوم `lambda_pred=0`
را انتخاب کرد. حتی `lambda_q=20` فقط 0.16 درصد CE سهم داشت. نسخه‌ی جداگانه‌ی
EMA-normalized سهم را به 8.6 درصد رساند، ولی validation accuracy را از 0.967 به 0.900
کاهش و PGD ASR را افزایش داد؛ بنابراین بدون test evaluation رد شد.

مدل نهایی test accuracy را از 0.8667 به 0.8333 کاهش داد. این افت بیش از معیار 2
percentage-point است و ادعای robustness تأیید نمی‌شود.

### Phase 15.2 — Paired sample analysis

اشتراک نمونه‌های clean-correct برابر 25 است. بهبود ظاهری PGD در epsilon=5% پس از حذف
تفاوت denominator کاملاً ناپدید شد. در epsilon=10% فقط یک نمونه rescue و صفر broken
وجود دارد. هیچ configuration بیش از net gain برابر +1 ندارد و exact McNemar p-valueها
برابر 1.0 هستند؛ بنابراین signal ضعیف و mixed است و ادعای robustness مجاز نیست.

### Phase 15.3 — Multi-seed replication

پروتکل frozen با `lambda_q=5` و `lambda_pred=0` برای seedهای
`42,123,777,2026,6543` روی split ثابت seed 42 تکرار شد. تغییر میانگین clean accuracy
صفر بود، ولی PGD ده‌درصد فقط در 2 از 5 seed و gradient TEMP-DRIFT ده‌درصد فقط در
1 از 5 seed بهبود داشت. هیچ sample ID بیش از یک بار rescue نشد. نتیجه seed-sensitive
است و robustness claim را پشتیبانی نمی‌کند.

### Phase 16 — Decision-aware QUANTUM-TEMP

Lossهای prediction JS و true-class margin اضافه شدند. JS همچنان بسیار کوچک بود؛ margin
gradient معنادار classifier داشت، ولی weightهای بزرگ clean validation را خراب کردند.
مدل JS+Margin+Quantum در seed 42 انتخاب شد، اما replication validation روی seedهای
42، 777 و 2026 gate را پاس نکرد. بنابراین test نهایی عمداً اجرا نشد و robustness claim
وجود ندارد.

---

## Phase 16 — Detection evaluation
Metrics:
- ROC-AUC
- TPR@fixed FPR
- FPR
- Detection rate

---

## Phase 17 — Shot ablation
```text
M = 100, 1000, 8192
```

---

## Phase 18 — Finish Iris
در این مرحله نتایج Iris باید کامل باشند.

حداقل:
1. Clean QSNN table
2. Depth ablation
3. Attack comparison
4. Epsilon/Tau sweep
5. Stealth table
6. Defense table
7. Shot ablation

---

## Phase 19 — MNIST
پس از تثبیت Iris:

```text
MNIST
→ downsample / dimensional reduction
→ 8 features
→ 8 spike times
→ 8 qubits
```

---

## Phase 20 — SHD
SHD مهم است چون native event/spike data دارد:

```text
SHD events
→ selected channels
→ real spike times
→ quantum encoding
→ QSNN
→ TEMP-DRIFT
```

---

## Phase 21 — Encoding ablation
سه encoding:
```text
Angle
Amplitude
Phase
```

هدف:
```text
3 datasets × 3 encodings = 9 configurations
```

---

## Phase 22 — Multi-seed
مثلاً:
```text
42
1234
7777
```

گزارش:
```text
mean ± std
```

---

## Phase 23 — Statistical analysis
مقایسه‌ها:
- TEMP-DRIFT vs Random
- TEMP-DRIFT vs Classical attack
- QUANTUM-TEMP vs Classical detector

---

## Phase 24 — Figures
حداقل:
1. Overall pipeline
2. QSNN architecture
3. Clean vs attacked spike train
4. Bloch drift
5. ASR vs epsilon
6. Quantum drift vs classical drift

---

## Phase 25 — Final scientific gate
قبل از نوشتن Results باید جواب عددی داشته باشیم:

1. آیا TEMP-DRIFT prediction را flip می‌کند؟
2. آیا quantum drift بالا می‌رود؟
3. آیا classical statistics تقریباً حفظ می‌شوند؟
4. آیا TEMP-DRIFT از random jitter بهتر است؟
5. آیا QUANTUM-TEMP حمله را تشخیص می‌دهد؟

---

# Phase Runner

برای تست یک فاز:

```bash
python phase_runner.py --phase 2
```

اگر موفق باشد:

```text
PHASE 2 PASSED
You can proceed to PHASE 3.
```

اگر fail شود:

```text
PHASE 2 FAILED
Do not proceed. Fix the failing tests first.
```

---

# شروع واقعی

```bash
pip install -r requirements.txt
python scripts/check_environment.py
python phase_runner.py --phase 1
python phase_runner.py --phase 2
python phase_runner.py --phase 3
python phase_runner.py --phase 4
python scripts/train_iris.py
```

فقط وقتی Clean QSNN درست شد وارد attack شوید.

> Iris در این پروژه sanity check است، نه benchmark اصلی برای ادعای SOTA classification.

### Phase 17 — Adversarial Timing Training

در این فاز یک PGD سبک و مستقل برای training اضافه شد (`epsilon=0.02T`، شروع از clean،
sign ascent و `alpha=epsilon/steps`). PGD-1 از PGD-3/5 بهتر بود. objective انتخاب‌شده
`CE(clean)+CE(adversarial)+0.5*margin` است. میانگین PGD validation در هر سه seed بهتر
شد، اما در دو seed دقت clean به اندازه 3.33 واحد درصد افت کرد و seed 2026 در epsilonهای
1% و 2% نمونه‌های جدیدی را شکست داد. gate چند-seed رد شد، test نهایی استفاده نشد و
robustness claim وجود ندارد.

### Phase 17.1 — کالیبراسیون وزن adversarial

PGD-1 و margin ثابت ماندند و فقط `lambda_adv` بررسی شد. همه وزن‌ها در seed 42 دقت
clean را حفظ کردند، اما 0.10/0.25 رفتار PGD در epsilon کوچک را بدتر کردند. وزن‌های
0.50/0.75 در seedهای 777 و 2026 همان افت clean و تغییر class-2 sample 119 را تکرار
کردند. gate چند-seed رد شد و test نهایی دست‌نخورده ماند.

### Phase 17.2 — تشخیص مرز class 1/2

trajectory هر epoch برای baseline و defense ثابت در سه seed بازسازی شد. sample 119 در
خود baseline نیز ناپایدار است و در defense به‌تدریج از مرز عبور می‌کند. انتخاب checkpoint
در seed 777 اثر دارد، اما seed 2026 فشردگی گسترده‌تر margin و centroid را نشان می‌دهد.
gradientهای clean CE، adversarial CE و margin هم‌جهت‌اند؛ شواهدی برای conflict مستقیم
objective وجود ندارد. defense تغییر نکرد و test استفاده نشد.
