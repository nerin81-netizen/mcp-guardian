# mcp-guardian

[English](./README.md) | [한국어](./README.ko.md) | [中文](./README.zh.md) | [日本語](./README.ja.md) | [Español](./README.es.md) | **Français** | [हिन्दी](./README.hi.md) | [العربية](./README.ar.md)

---

Firewall de confidentialité pour le développement avec IA. Empêche les secrets, PII et
mots-clés internes d'arriver sur GitHub quand un agent IA fait un commit.

## ✨ C'est quoi ça ?

**L'IA écrit du code.** Et elle fait des erreurs. Elle met des infos sensibles dans les commits,
expose des tokens dans les URLs distantes, ou balance des données perso dans le README.

Une fois que c'est sur GitHub, **y'a pas de retour en arrière**. C'est forké, caché, ça reste pour toujours.

`mcp-guardian` c'est ton **rempart à 4 couches** :

```bash
# ❌ Avant : attendre que l'IA se plante
IA hardcode une API key → push → découverte → panique → nettoyage d'historique → révocation du token

# ✅ Après : blocage préventif
IA hardcode une API key → check_files bloque direct → pas de commit → pas d'incident
```

**Comment ça marche en vrai :**

```text
IA : "Je vais sauvegarder ce fichier"
→ check_files("src/config.py")
→ 🔍 Scan en cours...
→ ❌ Détecté : pattern d'API key OpenAI (ligne 12)
→ Bloqué : le commit avance pas

IA : "Ah, merci. Je corrige."
```

## 🎯 Quand l'utiliser

**Scénario 1 : L'IA crée un fichier avec des infos sensibles**

```text
IA : "Je vais sauvegarder ce fichier de config"
→ check_files("config.py")

Résultat :
🔍 Résultat du scan — 2 fichiers, 1 problème

❌ config.py
   Ligne 12 : OPENAI_API_KEY = "«redacté:sk-…»..."
   → Détecté : pattern d'API key OpenAI
   → Bloqué

✅ Après correction :
   OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
   → ✅ Ça passe
```

**Scénario 2 : Vérifier tous les changements avant le commit**

```bash
# Vérifie automatiquement les fichiers staged
git add .
→ check_commit()

Résultat :
🔍 Vérification pre-commit — 5 fichiers

❌ README.md
   Ligne 45 : export GH_TOKEN=ghp_abc123...
   → Détecté : pattern de GitHub PAT
   → Commit bloqué

✅ Après correction et recommit :
   export GH_TOKEN=$GITHUB_TOKEN
   → ✅ Commit réussi
```

**Scénario 3 : Retracer des infos sensibles déjà poussées**

```text
"Hmm, je crois que j'ai poussé un token par erreur y'a un moment..."
→ sanitize_history()

Résultat :
🔍 Vérification de l'historique — 47 commits

❌ Trouvé : 1
   Commit : a1b2c3d (y'a 2 semaines)
   Fichier : .env
   Contenu : OPENAI_API_KEY = "sk-..."
   → Première exposition dans ce commit

Actions :
   1. Révoquer le token immédiatement
   2. Nettoyer l'historique avec git filter-branch
   3. Force push (attention !)
```

**Scénario 4 : Token dans l'URL distante**

```bash
git remote set-url origin https://***@github.com/user/repo.git
git push
→ check_remote_url()

Résultat :
❌ Token détecté dans l'URL distante
   Détecté : GitHub PAT (ghp_...)
   Correction auto : token retiré avant le push

✅ URL corrigée :
   https://github.com/user/repo.git
```

## Pourquoi ça existe

Les agents IA écrivent du code plus vite que les humains peuvent le relire.
Un seul token qui traîne ou un nom perso dans un README peut devenir un enregistrement
public permanent dès qu'un commit arrive sur GitHub. `mcp-guardian` c'est la
couche de défense qui choppe ces erreurs à quatre checkpoints :

1. **À l'édition** — `check_files` signale le contenu sensible avant de sauvegarder.
2. **Au commit** — `check_commit` ou le pre-commit hook bloque le commit complètement.
3. **Au push** — `check_remote_url` supprime les PATs qui ont fuité dans l'URL distante.
4. **À l'audit** — `sanitize_history` retrace les fuites passées jusqu'à leur commit d'origine.

## Sécurité récursive

Le serveur embarque ses propres règles de patterns dans `src/mcp_guardian/patterns.py`.
Ce fichier est en whitelist (avec `server.py` et les fixtures de test) donc
le guardian se bloque jamais lui-même quand il scanne son propre repo.

## Installer

```bash
pip install mcp-guardian
```

Ou depuis le source :

```bash
git clone https://github.com/nerin81-netizen/mcp-guardian
cd mcp-guardian
pip install -e .
```

## Le brancher

Dans la config de ton client MCP (ex : `claude_desktop_config.json` de Claude Code) :

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

Ensuite tu dis à ton agent :

> "Avant de committer, lance `check_commit` sur ce repo."

Ou installe le enforce au niveau OS et oublie-le :

```bash
mcp-guardian install-hook
```

Maintenant chaque `git commit` est protégé, même si l'agent oublie d'appeler l'outil.

## Catégories de règles

| Catégorie | Exemples détectés |
| --- | --- |
| Identifiants personnels | mots-clés d'entreprise / projet / nom perso |
| Tokens GitHub | `ghp_…`, `gho_…`, `github_pat_…` |
| Clés de providers | OpenAI, Anthropic, Slack, Google, AWS |
| Secrets génériques | assignations du genre `api_key = "…"` |
| Emails | adresses pas dans la whitelist |

Inspecte les règles actives via la ressource MCP :

```
resource: config://rules
```

## Licence

MIT — voir [LICENSE](./LICENSE).
