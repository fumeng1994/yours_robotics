## R&D memo (≤ 1 page)

Add a short memo (`RND_MEMO.md`) proposing **one** new capability for our robots that you
believe is worth building. We will assess it primarily on **commercial viability**: be clear
about **who would pay for it and why** (a venue owner, a brand running a campaign, the
operator), sketch how you would build it, and say how you would validate it in the PDD pilot.

---

I propose introducing "AI Fleet Insights"—an LLM-powered telemetry analysis capability embedded directly into the operator dashboard. 
A clean "Generate AI Insight" button at the top of the Fleet Overview and Per-Robot drill-down views. 
This feature goes beyond passive data display, instantly generating executive summaries, identifying latent technical faults, and delivering actionable operational recommendations.

### Commercial Viability: Who Pays and Why?
Who Pays: Fleet managers, robot operaters. User pays for a tiered B2B SaaS / Subscription model for access to advanced AI insights, high-level operational features, and cutting-edge R&D tools
- Non-technical operators save hours diagnosing why a robot is underperforming. The AI translates raw error anomalies into clear corrective steps
- Operational Optimization: The AI can detect subtle behavioral trends—such as a specific zone having high footfall but low QR conversion rates—and suggest moving a robot to a high-yield hotspot or adjusting the screen's digital campaign
- Technological Leadership: Offering cutting-edge, forward-thinking AI capabilities serves as a massive competitive differentiator for Yours Robotics during premium commercial bidding.


### Production Readiness & Pipeline Development
A baseline proof-of-concept has already been demonstrated in this application. To scale this feature safely into a production-ready environment, we will execute the following pipeline:
- Precision Prompt Engineering: Refine system prompts with strict constraints, explicitly instructing the LLM on which deterministic telemetry parameters to prioritize while defining boundaries where it can flexibly offer creative operational suggestions.
- Contextual Grounding Architecture: Rather than simply fine-tuning a model on terminology, we will implement industry-standard Retrieval-Augmented Generation (RAG) frameworks and structure our prompt context around key performance indicators like MTTR. This ensures the LLM is securely anchored in actual fleet data and Yours Robotics' unique operational guidelines.
- Engineering Verification & Audit: To guarantee insight accuracy, the engineering team will perform manual blind audits on historical pilot logs. We will benchmark the LLM’s outputs against verified human conclusions to eliminate hallucinations and ensure all recommendations strictly align with company business rules.


### Conclusion
While modern Large Language Models are inherently non-deterministic, their capacity for generalization makes them incredibly powerful tools when applied to complex operational data. When securely grounded by the specific business context of Yours Robotics, an LLM can uncover creative, highly sophisticated optimizations to improve business workflows—often highlighting operational blind spots that aren't immediately apparent to human experts

