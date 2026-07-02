# Use Groq API with Llama 3 8B for zero-cost inference

Both the classifier and judge use Llama 3 8B via the Groq API. Groq's free tier covers the entire project — no API cost at any scale within free limits. The Anthropic SDK is not used; instead, LangGraph integrates with Groq via LangChain's `ChatGroq` class, which supports `.with_structured_output()` and preserves the structured output guarantee from ADR-0001.

The trade-off accepted: Llama 3 8B is less capable than Claude Sonnet or Opus on nuanced classification. The retry + judge pipeline compensates for lower single-call reliability.
