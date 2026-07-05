# mcp-guardian

[English](./README.md) | [한국어](./README.ko.md) | [中文](./README.zh.md) | [日本語](./README.ja.md) | [Español](./README.es.md) | [Français](./README.fr.md) | **हिन्दी** | [العربية](./README.ar.md)

---

AI-पावर्ड डेवलपमेंट के लिए प्राइवेसी फायरवॉल। सीक्रेट्स, PII और
इंटरनल कीवर्ड्स को GitHub तक पहुँचने से रोकता है जब AI एजेंट कोड कमिट करता है।

## ✨ ये क्या है?

**AI कोड लिखता है।** और गलतियाँ करता है। कमिट्स में सेंसिटिव इंफो डाल देता है,
रिमोट URLs में टोकन्स एक्सपोज़ कर देता है, या README में पर्सनल डेटा डाल देता है।

एक बार GitHub पर चढ़ गया तो **वापसी नहीं है।** फोर्क हो जाता है, कैश हो जाता है, हमेशा रह जाता है।

`mcp-guardian` तुम्हारी **4-लेयर की ढाल** है:

```bash
# ❌ पहले: AI के गलती करने का इंतज़ार
AI हार्डकोड करता है API key → push → पकड़ा जाता है → पैनिक → हिस्ट्री क्लीन → टोकन रिवोक

# ✅ अब: प्रिवेंटिव ब्लॉक
AI हार्डकोड करता है API key → check_files तुरंत ब्लॉक → कमिट नहीं → इंसिडेंट नहीं
```

**असल में कैसे काम करता है:**

```text
AI: "ये फाइल सेव करूँगा"
→ check_files("src/config.py")
→ 🔍 स्कैन कर रहा है...
→ ❌ डिटेक्ट हुआ: OpenAI API key pattern (line 12)
→ ब्लॉक: कमिट आगे नहीं बढ़ता

AI: "अच्छा, थैंक्स। ठीक करता हूँ।"
```

## 🎯 कब यूज़ करें

**सीनारियो 1: AI सेंसिटिव इंफो वाली फाइल बनाता है**

```text
AI: "ये कॉन्फिग फाइल सेव करूँगा"
→ check_files("config.py")

रिजल्ट:
🔍 स्कैन रिजल्ट — 2 फाइल्स, 1 प्रॉब्लम

❌ config.py
   लाइन 12: OPENAI_API_KEY = "«रिडैक्टेड:sk-…»..."
   → डिटेक्ट हुआ: OpenAI API key pattern
   → ब्लॉक हुआ

✅ ठीक करने के बाद:
   OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
   → ✅ पास
```

**सीनारियो 2: कमिट से पहले सभी चेंजेस चेक करना**

```bash
# स्टेज्ड फाइल्स को ऑटोमैटिकली चेक करता है
git add .
→ check_commit()

रिजल्ट:
🔍 प्री-कमिट चेक — 5 फाइल्स

❌ README.md
   लाइन 45: export GH_TOKEN=ghp_abc123...
   → डिटेक्ट हुआ: GitHub PAT pattern
   → कमिट ब्लॉक

✅ ठीक करके फिर से कमिट:
   export GH_TOKEN=$GITHUB_TOKEN
   → ✅ कमिट सक्सेस
```

**सीनारियो 3: पहले से पुश की गई सेंसिटिव इंफो ट्रैक करना**

```text
"हम्म, लगता है मैंने गलती से कोई टोकन पुश किया था कुछ समय पहले..."
→ sanitize_history()

रिजल्ट:
🔍 हिस्ट्री चेक — 47 कमिट्स

❌ मिला: 1
   कमिट: a1b2c3d (2 हफ्ते पहले)
   फाइल: .env
   कंटेंट: OPENAI_API_KEY = "sk-..."
   → पहली एक्सपोज़र इस कमिट में

एक्शन:
   1. टोकन तुरंत रिवोक करो
   2. git filter-branch से हिस्ट्री क्लीन करो
   3. Force push (सावधानी से!)
```

**सीनारियो 4: रिमोट URL में टोकन शामिल हो गया**

```bash
git remote set-url origin https://***@github.com/user/repo.git
git push
→ check_remote_url()

रिजल्ट:
❌ रिमोट URL में टोकन डिटेक्ट
   डिटेक्ट हुआ: GitHub PAT (ghp_...)
   ऑटो करेक्शन: पुश से पहले टोकन हटाया

✅ करेक्ट की गई URL:
   https://github.com/user/repo.git
```

## क्यों बना

AI एजेंट्स इंसानों के रिव्यू करने की स्पीड से तेज़ कोड लिखते हैं।
एक भी लीक हुई क्रेडेंशियल या पर्सनल नाम README में GitHub पर
कमिट पहुँचते ही permanent public record बन सकता है। `mcp-guardian` वो
डिफेंस लेयर है जो इन गलतियों को चार चेकपॉइंट्स पर पकड़ता है:

1. **एडिट करते वक़्त** — `check_files` सेव करने से पहले सेंसिटिव कंटेंट फ्लैग करता है।
2. **कमिट करते वक़्त** — `check_commit` या pre-commit hook कमिट को पूरा ब्लॉक करता है।
3. **पुश करते वक़्त** — `check_remote_url` PATs को स्ट्रिप करता है जो रिमोट URL में लीक हुए।
4. **ऑडिट करते वक़्त** — `sanitize_history` पिछली लीक्स को उनके ओरिजिनल कमिट तक ट्रेस करता है।

## रिकर्सिव सेफ्टी

सरवर अपने pattern rules `src/mcp_guardian/patterns.py` में लाता है।
वो फाइल whitelist में है (`server.py` और टेस्ट फिक्स्चर्स के साथ) तो
गार्डियन कभी अपने आपको ब्लॉक नहीं करता जब वो अपने ही repo को स्कैन करता है।

## इंस्टॉल

```bash
pip install mcp-guardian
```

या सोर्स से:

```bash
git clone https://github.com/nerin81-netizen/mcp-guardian
cd mcp-guardian
pip install -e .
```

## कनेक्ट करो

अपने MCP क्लाइंट की कॉन्फिग में (जैसे Claude Code का `claude_desktop_config.json`):

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

फिर अपने एजेंट से कहो:

> "कमिट करने से पहले, इस repo पर `check_commit` रन करो।"

या OS-लेवल enforce एक बार इंस्टॉल करो और भूल जाओ:

```bash
mcp-guardian install-hook
```

अब हर `git commit` प्रोटेक्टेड है, भले ही एजेंट tool call करना भूल जाए।

## रूल कैटेगरीज़

| कैटेगरी | डिटेक्ट होने के उदाहरण |
| --- | --- |
| पर्सनल आइडेंटिफायर्स | कंपनी / प्रोजेक्ट / पर्सनल-नाम कीवर्ड्स |
| GitHub टोकन्स | `ghp_…`, `gho_…`, `github_pat_…` |
| प्रोवाइडर कीज़ | OpenAI, Anthropic, Slack, Google, AWS |
| जेनरिक सीक्रेट्स | `api_key = "…"` स्टाइल असाइनमेंट्स |
| ईमेल एड्रेसिस | non-allowlisted addresses |

लाइव रूल्स MCP रिसोर्स के ज़रिए देखो:

```
resource: config://rules
```

## लाइसेंस

MIT — देखो [LICENSE](./LICENSE).
