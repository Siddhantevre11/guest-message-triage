# Use structured output for classification response

The classifier must return a reliable `{ category, confidence, summary, suggested_action }` shape on every call. We use the Claude API's native structured output mechanism (tool use / `response_format`) rather than prompting for JSON and parsing the response. Prompt-only JSON is brittle — malformed output requires retry logic and validation that structured output eliminates at the API level. Reliability of the output schema is a first-class requirement for this system.
