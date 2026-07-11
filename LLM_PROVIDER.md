# JourneyIQ LLM Provider Configuration Guide

This document describes the environment variables, API setups, and fallback behaviors for third-party LLMs used by the AI Shopping Assistant.

---

## 1. Provider Fallback Priority

The assistant automatically checks configurations on every user request and selects providers in this order:
1.  **Google Gemini API** (Uses `google-generativeai` SDK, model: `gemini-1.5-flash`).
2.  **OpenAI API** (Uses `openai` client, model: `gpt-4o-mini`).
3.  **Local Offline Generator** (Standard template-driven offline responder matching intent).

---

## 2. Environment Variables Configuration

Copy and append these variables to your `.env` configuration:

```bash
# ----------------------------------------------------
# AI Assistant LLM Provider Keys
# ----------------------------------------------------

# Google Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your_openai_key_here
```

If neither `GEMINI_API_KEY` nor `OPENAI_API_KEY` is present, the chatbot will operate in **Offline Local Mode**, extracting matching items from your database and generating helpful template replies locally without making network calls.
