import { useEffect, useRef, useState } from "react";
import { ApiError, predictWaste, type PredictionResult } from "./api";

const MATERIAL_LABELS: Record<string, string> = {
  carton: "Carton",
  verre: "Verre",
  metal: "Métal",
  papier: "Papier",
  plastique: "Plastique",
  poubelle_generale: "Non recyclable",
};

type Status = "idle" | "loading" | "success" | "error";

function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)} %`;
}

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const cameraInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    setFile(selected);
    setResult(null);
    setErrorMessage(null);
    setStatus("idle");

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(selected ? URL.createObjectURL(selected) : null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;

    setStatus("loading");
    setErrorMessage(null);

    try {
      const prediction = await predictWaste(file);
      setResult(prediction);
      setStatus("success");
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Une erreur inattendue est survenue.");
      setStatus("error");
    }
  }

  function handleReset() {
    setFile(null);
    setResult(null);
    setErrorMessage(null);
    setStatus("idle");
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (cameraInputRef.current) cameraInputRef.current.value = "";
  }

  return (
    <div className="page">
      <header className="header">
        <p className="eyebrow">TriPhoto</p>
        <h1>Où jeter ce déchet ?</h1>
        <p className="lede">Prenez une photo, on vous dit dans quel bac le jeter.</p>
      </header>

      <main>
        <form onSubmit={handleSubmit} className="upload-form">
          <div className="field">
            <label htmlFor="photo-input">Choisir une photo</label>
            <input
              ref={fileInputRef}
              id="photo-input"
              name="photo"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleFileChange}
              aria-describedby="photo-hint"
            />
          </div>

          <div className="field">
            <label htmlFor="photo-input-camera">Ou prendre une photo directement</label>
            <input
              ref={cameraInputRef}
              id="photo-input-camera"
              name="photo-camera"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              capture="environment"
              onChange={handleFileChange}
              aria-describedby="photo-hint"
            />
            <p id="photo-hint" className="hint">
              Formats acceptés : JPEG, PNG, WebP. 8 Mo maximum. Sur mobile, le second champ ouvre l'appareil photo directement.
            </p>
          </div>

          {previewUrl && (
            <div className="preview">
              <img src={previewUrl} alt={file ? `Aperçu de la photo sélectionnée : ${file.name}` : ""} />
            </div>
          )}

          <div className="actions">
            <button type="submit" disabled={!file || status === "loading"}>
              {status === "loading" ? "Analyse en cours…" : "Identifier ce déchet"}
            </button>
            {(file || result) && (
              <button type="button" className="secondary" onClick={handleReset}>
                Recommencer
              </button>
            )}
          </div>
        </form>

        <div role="status" aria-live="polite" className="result-region">
          {status === "loading" && <p className="loading">Analyse de la photo…</p>}

          {status === "error" && errorMessage && (
            <p className="error" role="alert">
              {errorMessage}
            </p>
          )}

          {status === "success" && result && (
            <article className="result">
              <p className="result-label">{MATERIAL_LABELS[result.label] ?? result.label}</p>
              <p className="result-hint">{result.disposalHint}</p>

              <ul className="confidence-bars">
                {result.topPredictions.map((prediction) => (
                  <li key={prediction.label}>
                    <div className="confidence-bar-row">
                      <span>{MATERIAL_LABELS[prediction.label] ?? prediction.label}</span>
                      <span>{formatConfidence(prediction.confidence)}</span>
                    </div>
                    <div className="confidence-bar-track">
                      <div
                        className="confidence-bar-fill"
                        style={{ width: formatConfidence(prediction.confidence) }}
                      />
                    </div>
                  </li>
                ))}
              </ul>
            </article>
          )}
        </div>
      </main>

      <footer className="footer">
        <img src="/qr-triphoto-app.png" alt="QR code vers cette application" width="72" height="72" />
        <p>Scannez pour essayer sur votre téléphone</p>
        <p>Projet TriPhoto — RNCP37827, épreuves E3 et E4.</p>
      </footer>
    </div>
  );
}
