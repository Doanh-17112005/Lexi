# AI Provider Setup Guide (`ai-service`)

Non-secret configuration reference for enabling LLM providers in `ai-service/.env` (or container environment variables). **Never commit real API keys or print secret values in logs or CI.**

## 1. Provider Routing Summary

- **Primary streaming & TraceCAG chat (`Lexi Chat`, `Topic Chat`)**: `Groq` (first) → `Gemini` (fallback) → `Ollama` (last resort, only when explicitly enabled).
- **Empty / disabled keys**: When no provider is configured, `ai-service` does **not** fabricate LLM output — it returns honest fallback responses (`SAFE_TUTOR_FALLBACK` / `SAFE_FIXED_RESPONSE`) with `model_used="safe_tutor_fallback"` or `"trace-cag_safe_response"`, and `diagnose_node` reports `models_used=["rule_fallback"]`.
- **Duplex voice (`VOICE_DUPLEX_ENABLED=true`)**: Requires Redis, STT engine (`faster-whisper` / registry ready), TTS (`piper`), and at least one Groq key (`GROQ_API_KEY` or `GROQ_API_KEYS`). When `VOICE_DUPLEX_ENABLED=false`, `/api/v1/voice/ready` returns HTTP `503` (`{"ready": false, "status": "disabled"}`) and `/api/v1/voice/ticket` returns HTTP `404`.

## 2. Environment Variables (Placeholders Only)

### Gemini (Google AI)
```dotenv
GEMINI_API_KEY=<set-your-gemini-api-key>
GEMINI_MODEL=gemini-2.5-flash
```
- Used by TraceCAG `generate_node`, `stream_llm_tokens`, and `TopicLLMGateway`.
- Supports multi-turn conversation history via `contents` (`user`/`model`) and `systemInstruction`.

### Groq (Fast Inference & IELTS Grader / Voice Duplex)
```dotenv
# Single key or comma-separated key pool for round-robin rate-limit distribution:
GROQ_API_KEY=<set-your-groq-api-key>
# GROQ_API_KEYS=<key1>,<key2>,<key3>
GROQ_MODEL=qwen/qwen3.6-27b
```
- `resolve_groq_model()` automatically skips retired models and enforces `reasoning_effort="none"` on Qwen3 models so `<think>` tokens do not consume `max_tokens`.

### Ollama (Optional Local Inference)
```dotenv
OLLAMA_ENABLED=false
USE_OLLAMA=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=lexilingo-qwen3-1.7b
```
- Keep both `OLLAMA_ENABLED=false` and `USE_OLLAMA=false` unless a local Ollama server is running at `OLLAMA_BASE_URL`.
- When enabled, ensure the model is pulled locally: `ollama pull lexilingo-qwen3-1.7b`.

## 3. Boolean Verification Commands (No Secret Output)

### Live HTTP Health Check
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/health" -Method Get | ConvertTo-Json -Depth 4
```
Expected shape:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "providers": {
    "groq_configured": false,
    "gemini_configured": false,
    "ollama_enabled": false
  }
}
```
Also check Topic/TraceCAG readiness:
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/v1/topics/llm/health" -Method Get | ConvertTo-Json -Depth 4
```

### Local `.env` Boolean Check (Safe — Never Prints Key Values)
```powershell
Get-Content D:\LexiLingo\LexiLingo\ai-service\.env |
  Where-Object { $_ -match "^(GEMINI_API_KEY|GROQ_API_KEY|GROQ_API_KEYS|OLLAMA_ENABLED|USE_OLLAMA|VOICE_DUPLEX_ENABLED)=" } |
  ForEach-Object {
    $k, $v = $_ -split "=", 2
    if ($k -match "KEY") { "$k=$([bool]$v.Trim())" } else { "$k=$($v.Trim())" }
  }
```
