# mcp-guardian

[English](./README.md) | [한국어](./README.ko.md) | [中文](./README.zh.md) | [日本語](./README.ja.md) | [Español](./README.es.md) | [Français](./README.fr.md) | [हिन्दी](./README.hi.md) | **العربية**

---

جدار خصوصية للتطوير بالذكاء الاصطناعي. يمنع الأسرار ومعلومات PII و
الكلمات المفتاحية الداخلية من الوصول لـ GitHub لما وكيل AI يعمل commit.

## ✨ إيه ده؟

**الذكاء الاصطناعي بيكتب كود.** وبيغلط. بيحط معلومات حساسة في commits،
وبيفضح tokens في remote URLs، أو بيحط بيانات شخصية في الـ README.

لما تطلع على GitHub **مفيش رجعة.** بتتعملها fork، وبتتخزن، وبتفضل للأبد.

`mcp-guardian` ده **جدارك الدفاعي بـ 4 طبقات**:

```bash
# ❌ قبل: نستنى لحد ما الـ AI يغلط
AI بيحط API key → push → حد اكتشف → ذعر → تنظيف التاريخ → إلغاء الـ token

# ✅ بعد: منع مسبق
AI بيحط API key → check_files بيمنع فوراً → مفيش commit → مفيش حادثة
```

**إزاي بيشتغل عملياً:**

```text
AI: "هحفظ الفايل ده"
→ check_files("src/config.py")
→ 🔍 بيفحص...
→ ❌ اتكشف: نمط API key لـ OpenAI (سطر 12)
→ اتمنع: الـ commit مش بيكمل

AI: "آه، شكراً. هظبطن."
```

## 🎯 إمتى تستخدمه

**السيناريو 1: الـ AI بيعمل فايل فيه معلومات حساسة**

```text
AI: "هحفظ فايل الـ config ده"
→ check_files("config.py")

النتيجة:
🔍 نتيجة الفحص — 2 فايلات، مشكلة واحدة

❌ config.py
   سطر 12: OPENAI_API_KEY = "«محذوف:sk-…»..."
   → اتكشف: نمط API key لـ OpenAI
   → اتمنع

✅ بعد التصحيح:
   OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
   → ✅ اتقبل
```

**السيناريو 2: فحص كل التغييرات قبل الـ commit**

```bash
# بيفحص الـ staged files تلقائياً
git add .
→ check_commit()

النتيجة:
🔍 فحص pre-commit — 5 فايلات

❌ README.md
   سطر 45: export GH_TOKEN=ghp_abc123...
   → اتكشف: نمط GitHub PAT
   → الـ commit اتمنع

✅ بعد التصحيح والـ commit تاني:
   export GH_TOKEN=$GITHUB_TOKEN
   → ✅ الـ commit نجح
```

**السيناريو 3: تتبع معلومات حساسة اتعملها push قبل كده**

```text
"هممم، فاكر إني عملت push لـ token بالغلط من زمان..."
→ sanitize_history()

النتيجة:
🔍 فحص التاريخ — 47 commit

❌ اتلاقى: 1
   Commit: a1b2c3d (من أسبوعين)
   فايل: .env
   المحتوى: OPENAI_API_KEY = "sk-..."
   → أول ظهور كان في الـ commit ده

الإجراءات:
   1. إلغاء الـ token فوراً
   2. تنظيف التاريخ بـ git filter-branch
   3. Force push (بحذر!)
```

**السيناريو 4: Token داخل في الـ remote URL**

```bash
git remote set-url origin https://***@github.com/user/repo.git
git push
→ check_remote_url()

النتيجة:
❌ Token اتكشف في الـ remote URL
   اتكشف: GitHub PAT (ghp_...)
   تصحيح تلقائي: الـ token اتشال قبل الـ push

✅ الـ URL بعد التصحيح:
   https://github.com/user/repo.git
```

## ليه موجود

وكلاء AI بيكتبوا كود أسرع من ما البشر يقدروا يراجعه.
أي اعتمادية واحدة سايبة أو اسم شخصي في README ممكن يبقى سجل عام دائم
لحظة ما الـ commit يوصل لـ GitHub. `mcp-guardian` هو
طبقة الدفاع اللي بتلتقط الغلطات دي في أربع نقاط تفتيش:

1. **وقت التحرير** — `check_files` بيحدد المحتوى الحساس قبل الحفظ.
2. **وقت الـ commit** — `check_commit` أو الـ pre-commit hook بيمنع الـ commit تماماً.
3. **وقت الـ push** — `check_remote_url` بيشيل PATs اللي سربت في الـ remote URL.
4. **وقت المراجعة** — `sanitize_history` بيرجع يتتبع التسريبات القديمة لأصل الـ commit بتاعها.

## أمان عودي

السيرفر جاي بقواعد الأنماط بتاعته في `src/mcp_guardian/patterns.py`.
الفايل ده في الـ whitelist (مع `server.py` و fixtures الاختبار) فالـ
guardian مش بيمنع نفسه لما بيفحص الـ repo بتاعه.

## التثبيت

```bash
pip install mcp-guardian
```

أو من الـ source:

```bash
git clone https://github.com/nerin81-netizen/mcp-guardian
cd mcp-guardian
pip install -e .
```

## التوصيل

في إعدادات عميل MCP بتاعك (مثلاً `claude_desktop_config.json` لـ Claude Code):

```json
{
  "mcpServers": {
    "guardian": {
      "command": "python",
      "args": ["-m", "mcp_guardian.server"]
    }
  }
}
```

وبعدين قول للـ agent بتاعك:

> "قبل ما تعمل commit، شغل `check_commit` على الـ repo ده."

أو ثبّت المنع على مستوى الـ OS مرة واحدة وانسى:

```bash
mcp-guardian install-hook
```

دلوقتي كل `git commit` محمي، حتى لو الـ agent نسي يستدعي الأداة.

## فئات القواعد

| الفئة | أمثلة مكتشفة |
| --- | --- |
| معرفات شخصية | كلمات مفتاحية لشركة / مشروع / اسم شخصي |
| توكنات GitHub | `ghp_…`, `gho_…`, `github_pat_…` |
| مفاتيح المزودين | OpenAI, Anthropic, Slack, Google, AWS |
| أسرار عامة | تعيينات زي `api_key = "…"` |
| عناوين إيميل | عناوين مش في الـ whitelist |

شوف القواعد الحية عن طريق مورد MCP:

```
resource: config://rules
```

## الترخيص

MIT — شوف [LICENSE](./LICENSE).
