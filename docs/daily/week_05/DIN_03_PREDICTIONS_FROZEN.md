# Week 5 Din 3 — FROZEN PREDICTIONS

## Q1 (Step 1 se pehle)
`git ls-files` ki poori list lo aur usko `git check-ignore --no-index --stdin`
se guzaro. Kitni tracked files ko ek ignore pattern ALREADY match karta hai —
ek number likho.
Aur: wo files kaunsi class ki hain? Unme se ek document NAHI hai aur usko kabhi
commit nahi hona chahiye tha — kaunsi tarah ki file hogi, aur wo abhi bhi tracked
kyun hai? Mechanism ek line me.

### Prediction
idk

## Q2 (Step 3 se pehle)
Maano tu `.gitignore` me `**/daily/` rakhta hai aur uske neeche do line add karta
hai: `!**/daily/**/*BRIEF*` aur `!**/daily/**/*PREDICTIONS_FROZEN*`.
`git add -A --dry-run` chalane pe `DIN_03_BRIEF.md` us output me aayega ya nahi?
Haan/nahi, aur mechanism.
Aur doosra half: agar nahi aayega, to kya do line ka ORDER badalne se aa jaayega?
Ya koi bhi order kaam nahi karega? Kyun.

### Prediction
idk

## Q3 (Step 3 se pehle)
Maano kisi din ek sealed KEY galti se `git add -f` se add hui aur commit ho gayi.
Aaj tu `git check-ignore -v docs/daily/week_05/DIN_02_KEY.md` chalata hai (bina
--no-index). Exit code `0` aayega ya `1`, aur kya wo koi line print karega?
Aur: uske baad `git rm --cached` + commit karne se us KEY ka CONTENT repository se
chala jaata hai, ya nahi? Ek shabd, aur mechanism.

### Prediction
idk

## Q4 (Step 4 se pehle)
Din 1 ne apna exception probe `labs/w5d1_exc_probe.py` me rakha. Din 2 ne apne
paanch harness `scratch/` me rakhe. Ek hi hafta, ek hi repo.
Dono me se kaunsa git me hai? Aur wo faisla kisne kiya — ek line.
Aur teesra, aur ye wala sabse ulta jawab de sakta hai: `scratch/step6_harness.ps1`
— wahi harness jisko `P-50` Din 1 ki evidence maarne ka zimmedaar batata hai — kya
wo AAJ repository se padhi ja sakti hai? Haan/nahi, aur kahan se.

### Prediction
idk

## Q5 (Step 6 se pehle)
`requirements.txt` me gyarah declared deps hain.
`pip freeze` kitni line degi — ek number.
`pip list --not-required --format=freeze` kitni line degi — ek number.
Aur asli sawaal: doosri list wale gyarah, kya WAHI gyarah hain jo requirements.txt
me hain? Agar nahi, to kaunsi missing hain aur kaunsi extra hai — aur missing wali
ka MECHANISM kya hai (wo install hi hain, to list me kyun nahi aayi)?

### Prediction
idk
