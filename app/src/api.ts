/** Client de l'API TriPhoto : authentification (avec renouvellement de token, C10)
 * et appel de /predict. */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const DEMO_CLIENT_ID = import.meta.env.VITE_DEMO_CLIENT_ID ?? "demo-agent";
const DEMO_CLIENT_SECRET = import.meta.env.VITE_DEMO_CLIENT_SECRET ?? "change-me-too";

export class ApiError extends Error {}

interface TokenPair {
  accessToken: string;
  refreshToken: string;
}

export interface PredictionResult {
  label: string;
  confidence: number;
  modelVersion: string;
  disposalHint: string;
}

let cachedTokens: TokenPair | null = null;

async function login(): Promise<TokenPair> {
  const response = await fetch(`${API_BASE}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: DEMO_CLIENT_ID, client_secret: DEMO_CLIENT_SECRET }),
  });
  if (!response.ok) {
    throw new ApiError("Impossible de s'authentifier auprès de l'API.");
  }
  const data = await response.json();
  return { accessToken: data.access_token, refreshToken: data.refresh_token };
}

async function refresh(refreshToken: string): Promise<TokenPair> {
  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) {
    throw new ApiError("La session a expiré, merci de réessayer.");
  }
  const data = await response.json();
  return { accessToken: data.access_token, refreshToken: data.refresh_token };
}

async function ensureTokens(): Promise<TokenPair> {
  if (!cachedTokens) {
    cachedTokens = await login();
  }
  return cachedTokens;
}

async function callPredict(file: File, accessToken: string): Promise<Response> {
  const formData = new FormData();
  formData.append("file", file);
  return fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
    body: formData,
  });
}

async function toPredictionResult(response: Response): Promise<PredictionResult> {
  const data = await response.json();
  return {
    label: data.label,
    confidence: data.confidence,
    modelVersion: data.model_version,
    disposalHint: data.disposal_hint,
  };
}

async function readErrorCode(response: Response): Promise<string | undefined> {
  try {
    const body = await response.json();
    return typeof body?.detail === "object" ? body.detail.error : undefined;
  } catch {
    return undefined;
  }
}

/** Envoie la photo à l'API. Renouvelle automatiquement le token si l'API
 * répond 401 {"error": "token_expired"} — c'est le comportement attendu par C10. */
export async function predictWaste(file: File): Promise<PredictionResult> {
  const tokens = await ensureTokens();
  let response = await callPredict(file, tokens.accessToken);

  if (response.status === 401) {
    const errorCode = await readErrorCode(response);
    if (errorCode === "token_expired") {
      cachedTokens = await refresh(tokens.refreshToken);
      response = await callPredict(file, cachedTokens.accessToken);
    }
  }

  if (!response.ok) {
    throw new ApiError(
      response.status === 415
        ? "Format d'image non supporté. Utilisez une photo JPEG, PNG ou WebP."
        : "La prédiction a échoué. Réessayez avec une autre photo.",
    );
  }

  return toPredictionResult(response);
}
