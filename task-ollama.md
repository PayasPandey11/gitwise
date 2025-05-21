> **Note:** Ollama should be the default backend for local LLM inference in GitWise.

# Feature: Integrate Ollama as LLM Backend

## Goal
Enable GitWise to use Ollama for local LLM inference, improving speed and efficiency.

## Tasks
- [ ] Research Ollama API and local integration requirements
- [ ] Design backend selection logic (env/config/CLI)
- [ ] Implement Ollama backend module (e.g., `gitwise/llm/ollama.py`)
- [ ] Add backend selection to LLM router
- [ ] Add tests for Ollama backend
- [ ] Update documentation (README, usage, etc.)
- [ ] Manual test: commit, PR, changelog with Ollama
- [ ] (Optional) Add CLI command to check Ollama status

## Out of Scope
- Removing existing offline/online backends
- Refactoring unrelated LLM logic

## Notes & Decisions
- User should be able to select backend via env/config/CLI 