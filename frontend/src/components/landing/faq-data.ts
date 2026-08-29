export interface FaqItem {
  q: string
  a: string
}

/* Real answers, no marketing inflation. Kept factual because this feeds both
   the on-page FAQ and the FAQPage JSON-LD that answer engines read. */
export const FAQ_ITEMS: FaqItem[] = [
  {
    q: "Is this a real simulation or a single chatbot with personas?",
    a: "Each role is a separate agent with its own knowledge scope, behavioural constraints, and model. They take turns, object, cross-examine, and cite evidence independently. The orchestrator manages turn order and can spawn a specialist agent mid-proceeding when a technical question opens up. It is a graph of agents, not one model role-playing.",
  },
  {
    q: "Where do the arguments come from? Can I trust the citations?",
    a: "Every agent argues from evidence you attach to the case. Retrieval is scoped by role, so a witness only sees its linked exhibits while the judge sees the whole record. Claims carry inline markers that resolve to the exact passage, audio timestamp, or video frame they came from, and each turn is labelled cited, inferred, or disputed.",
  },
  {
    q: "Which models does it use?",
    a: "Each legal role has a default provider and model, and you can override either per agent. It supports OpenAI, Anthropic, Google Gemini, and local models via Ollama. A single free provider can carry an entire proceeding.",
  },
  {
    q: "Can it run offline or on my own infrastructure?",
    a: "Yes. Nyayrithm is self-hostable and provider-agnostic. A full proceeding runs on a laptop with SQLite, a local vector store, sentence-transformers embeddings, and a local Ollama model, with no external calls. The LLM, database, vector store, file storage, and embedder are each one environment variable.",
  },
  {
    q: "What can I use it for?",
    a: "Litigators use it to stress-test a theory of the case and rehearse cross-examination before trial or deposition. Legal researchers use it to study multi-agent argumentation and evidence-grounded reasoning. It runs three modes: courtroom, deposition, and strategy session.",
  },
  {
    q: "Can I edit what an agent says?",
    a: "Yes. Any turn can be overridden with your own text; the override is marked on the record and the proceeding continues from it.",
  },
]
