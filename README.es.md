# mcp-guardian

[English](./README.md) | [한국어](./README.ko.md) | [中文](./README.zh.md) | [日本語](./README.ja.md) | **Español** | [Français](./README.fr.md) | [हिन्दी](./README.hi.md) | [العربية](./README.ar.md)

---

Firewall de privacidad para desarrollo con IA. Evita que secretos, PII y
keywords internas lleguen a GitHub cuando un agente de IA hace commit.

## ✨ Qué es esto

**La IA escribe código.** Y comete errores. Mete información sensible en commits,
expone tokens en URLs remotas, o pone datos personales en el README.

Una vez que sube a GitHub, **no hay vuelta atrás**. Se forkea, se cachea, queda para siempre.

`mcp-guardian` es tu **muralla de 4 capas**:

```bash
# ❌ Antes: esperar a que la IA se equivoque
IA hardcodea API key → push → descubren → pánico → limpiar historial → revocar token

# ✅ Después: bloqueo preventivo
IA hardcodea API key → check_files bloquea al instante → no hay commit → no hay incidente
```

**Cómo funciona en la práctica:**

```text
IA: "Voy a guardar este archivo"
→ check_files("src/config.py")
→ 🔍 Escaneando...
→ ❌ Detectado: patrón de API key de OpenAI (línea 12)
→ Bloqueado: el commit no avanza

IA: "Ah, gracias. Lo corrijo."
```

## 🎯 Cuándo usarlo

**Escenario 1: La IA crea un archivo con información sensible**

```text
IA: "Voy a guardar este archivo de configuración"
→ check_files("config.py")

Resultado:
🔍 Resultado del escaneo — 2 archivos, 1 problema

❌ config.py
   Línea 12: OPENAI_API_KEY = "«redactado:sk-…»..."
   → Detectado: patrón de API key de OpenAI
   → Bloqueado

✅ Después de corregir:
   OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
   → ✅ Pasa
```

**Escenario 2: Revisar todos los cambios antes del commit**

```bash
# Revisa automáticamente los archivos staged
git add .
→ check_commit()

Resultado:
🔍 Revisión pre-commit — 5 archivos

❌ README.md
   Línea 45: export GH_TOKEN=ghp_abc123...
   → Detectado: patrón de GitHub PAT
   → Commit bloqueado

✅ Después de corregir y volver a commitear:
   export GH_TOKEN=$GITHUB_TOKEN
   → ✅ Commit exitoso
```

**Escenario 3: Rastrear información sensible ya pusheada**

```text
"Hmm, creo que pusheé un token por error hace un tiempo..."
→ sanitize_history()

Resultado:
🔍 Revisión de historial — 47 commits

❌ Encontrado: 1
   Commit: a1b2c3d (hace 2 semanas)
   Archivo: .env
   Contenido: OPENAI_API_KEY = "sk-..."
   → Primera exposición en este commit

Acciones:
   1. Revocar el token inmediatamente
   2. Limpiar historial con git filter-branch
   3. Force push (¡con cuidado!)
```

**Escenario 4: Token incluido en la URL remota**

```bash
git remote set-url origin https://***@github.com/user/repo.git
git push
→ check_remote_url()

Resultado:
❌ Token detectado en la URL remota
   Detectado: GitHub PAT (ghp_...)
   Corrección automática: token eliminado antes del push

✅ URL corregida:
   https://github.com/user/repo.git
```

## Por qué existe

Los agentes de IA escriben código más rápido de lo que los humanos pueden revisar.
Una sola credencial suelta o nombre personal en un README puede volverse un registro
público permanente en el momento que un commit llega a GitHub. `mcp-guardian` es la
capa de defensa que detecta estos errores en cuatro puntos de control:

1. **Al editar** — `check_files` marca contenido sensible antes de guardar.
2. **Al commitear** — `check_commit` o el pre-commit hook bloquean el commit completamente.
3. **Al pushear** — `check_remote_url` elimina PATs que se filtraron en la URL remota.
4. **Al auditar** — `sanitize_history` rastrea fugas pasadas hasta su commit original.

## Seguridad recursiva

El servidor trae sus propias reglas de patrones en `src/mcp_guardian/patterns.py`.
Ese archivo está en whitelist (junto con `server.py` y fixtures de test) así
el guardian nunca se bloquea a sí mismo cuando escanea su propio repositorio.

## Instalar

```bash
pip install mcp-guardian
```

O desde el source:

```bash
git clone https://github.com/nerin81-netizen/mcp-guardian
cd mcp-guardian
pip install -e .
```

## Conectarlo

En la config de tu cliente MCP (ej: `claude_desktop_config.json` de Claude Code):

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

Después le decís a tu agente:

> "Antes de commitear, ejecutá `check_commit` en este repo."

O instalá la enforce a nivel de OS y olvidate:

```bash
mcp-guardian install-hook
```

Ahora cada `git commit` está protegido, incluso si el agente se olvida de llamar la herramienta.

## Categorías de reglas

| Categoría | Ejemplos detectados |
| --- | --- |
| Identificadores personales | keywords de empresa / proyecto / nombre personal |
| Tokens de GitHub | `ghp_…`, `gho_…`, `github_pat_…` |
| Keys de providers | OpenAI, Anthropic, Slack, Google, AWS |
| Secretos genéricos | asignaciones tipo `api_key = "…"` |
| Emails | direcciones no incluídas en whitelist |

Inspeccioná las reglas activas via el recurso MCP:

```
resource: config://rules
```

## Licencia

MIT — ver [LICENSE](./LICENSE).
