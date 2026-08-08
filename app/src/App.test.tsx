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
  const input = screen.getByLabelText(/photo du déchet/i) as HTMLInputElement;
  const file = new File(["fake-bytes"], "bouteille.jpg", { type: "image/jpeg" });
  fireEvent.change(input, { target: { files: [file] } });
  return file;
}

beforeEach(() => {
  mockedPredictWaste.mockReset();
});

describe("App", () => {
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
    });

    render(<App />);
    selectAFile();
    fireEvent.click(screen.getByRole("button", { name: /identifier ce déchet/i }));

    await waitFor(() => expect(screen.getByText("Bac à verre")).toBeInTheDocument());
    expect(screen.getByText("Verre")).toBeInTheDocument();
    expect(screen.getByText(/87 %/)).toBeInTheDocument();
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
