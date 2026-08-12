import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { ApiError, predictWaste } from "./api";

vi.mock("./api", async () => {
  const actual = await vi.importActual<typeof import("./api")>("./api");
  return { ...actual, predictWaste: vi.fn() };
});

const mockedPredictWaste = vi.mocked(predictWaste);

function selectAFile() {
  const input = screen.getByLabelText(/choisir une photo/i) as HTMLInputElement;
  const file = new File(["fake-bytes"], "bouteille.jpg", { type: "image/jpeg" });
  fireEvent.change(input, { target: { files: [file] } });
  return file;
}

beforeEach(() => {
  mockedPredictWaste.mockReset();
});

describe("App", () => {
  it("propose un champ de galerie et un champ caméra distincts", () => {
    render(<App />);
    const gallery = screen.getByLabelText(/choisir une photo/i) as HTMLInputElement;
    const camera = screen.getByLabelText(/prendre une photo directement/i) as HTMLInputElement;
    expect(gallery).not.toBe(camera);
    expect(camera.getAttribute("capture")).toBe("environment");
  });

  it("active le bouton quand la photo vient du champ caméra", () => {
    render(<App />);
    const camera = screen.getByLabelText(/prendre une photo directement/i) as HTMLInputElement;
    const file = new File(["fake-bytes"], "photo-live.jpg", { type: "image/jpeg" });
    fireEvent.change(camera, { target: { files: [file] } });
    expect(screen.getByRole("button", { name: /identifier ce déchet/i })).toBeEnabled();
  });

  it("désactive le bouton tant qu'aucune photo n'est choisie", () => {
    render(<App />);
    expect(screen.getByRole("button", { name: /identifier ce déchet/i })).toBeDisabled();
  });

  it("active le bouton une fois une photo sélectionnée", () => {
    render(<App />);
    selectAFile();
    expect(screen.getByRole("button", { name: /identifier ce déchet/i })).toBeEnabled();
  });

  it("affiche le résultat renvoyé par l'API après soumission", async () => {
    mockedPredictWaste.mockResolvedValue({
      label: "verre",
      confidence: 0.87,
      modelVersion: "waste_classifier-v1-mobilenetv3",
      disposalHint: "Bac à verre",
      topPredictions: [
        { label: "verre", confidence: 0.87 },
        { label: "plastique", confidence: 0.09 },
        { label: "metal", confidence: 0.04 },
      ],
    });

    render(<App />);
    selectAFile();
    fireEvent.click(screen.getByRole("button", { name: /identifier ce déchet/i }));

    await waitFor(() => expect(screen.getByText("Bac à verre")).toBeInTheDocument());
    // "Verre" apparaît deux fois : le résultat principal + la 1ère ligne du top-3
    expect(screen.getAllByText("Verre").length).toBe(2);
    expect(screen.getAllByText(/87 %/).length).toBeGreaterThan(0);
    // les deux alternatives du top-3 sont aussi affichées avec leur propre barre
    expect(screen.getByText("Plastique")).toBeInTheDocument();
    expect(screen.getByText(/9 %/)).toBeInTheDocument();
  });

  it("affiche un message d'erreur explicite si l'API échoue", async () => {
    mockedPredictWaste.mockRejectedValue(new ApiError("La prédiction a échoué. Réessayez avec une autre photo."));

    render(<App />);
    selectAFile();
    fireEvent.click(screen.getByRole("button", { name: /identifier ce déchet/i }));

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(/prédiction a échoué/i));
  });

  it("réinitialise le formulaire au clic sur Recommencer", async () => {
    mockedPredictWaste.mockResolvedValue({
      label: "carton",
      confidence: 0.9,
      modelVersion: "waste_classifier-v1-mobilenetv3",
      disposalHint: "Bac jaune (tri sélectif)",
      topPredictions: [{ label: "carton", confidence: 0.9 }],
    });

    render(<App />);
    selectAFile();
    fireEvent.click(screen.getByRole("button", { name: /identifier ce déchet/i }));
    await waitFor(() => expect(screen.getByText("Bac jaune (tri sélectif)")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /recommencer/i }));

    expect(screen.queryByText("Bac jaune (tri sélectif)")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /identifier ce déchet/i })).toBeDisabled();
  });
});
