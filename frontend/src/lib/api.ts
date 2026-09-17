/**
 * Frontend API helper for Darukaa conversation.
 *
 * The backend provides a FastAPI endpoint:
 *   POST ${import.meta.env.VITE_API_URL}/api/v1/conversation/turn
 * expecting a JSON body matching `ConversationRequest`:
 *   { conversation_id: string, message: string }
 * and returning a `ConversationResponse` with fields:
 *   conversation_id, status, message, environment?, recommendation?
 */

export type ConversationRequest = {
  conversation_id: string;
  message: string;
};

export type ConversationResponse = {
  conversation_id: string;
  status: string; // "needs_clarification" | "complete"
  message: string;
  environment?: any; // matches backend EnvironmentInput shape
  recommendation?: any; // matches backend RecommendationOutput shape
};

/**
 * Post a user message to the backend and obtain the assistant response.
 *
 * @param payload - The conversation request payload.
 * @returns The parsed JSON response from the backend.
 */
export async function postConversationTurn(
  payload: ConversationRequest,
): Promise<ConversationResponse> {
  const base = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
  const url = `${base.replace(/\/*$/, "")}/api/v1/conversation/turn`;

  const resp = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Failed to call conversation endpoint: ${resp.status} ${resp.statusText}\n${text}`);
  }

  const data = (await resp.json()) as ConversationResponse;
  return data;
}
