# LLM judge sits inline as a hard gate between classifier and router

Every classification passes through a second LLM call (the judge) before reaching a handler. The judge receives the message, category, and confidence from the classifier. It rejects if confidence < 0.7, and independently re-evaluates the category assignment regardless of confidence. Nothing reaches a handler without judge approval — escalation is the only downstream path for a rejected message.

We chose an inline gate rather than an optional validation step because bad classifications reaching handlers have real consequences (a complaint misrouted as small talk, a maintenance issue ignored). The cost of an extra LLM call per message is worth the guarantee that no unverified output propagates downstream.
