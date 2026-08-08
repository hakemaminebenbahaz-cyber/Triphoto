import "@testing-library/jest-dom/vitest";

// jsdom n'implémente pas l'API Blob URL utilisée pour l'aperçu de la photo (App.tsx).
if (typeof URL.createObjectURL !== "function") {
  URL.createObjectURL = () => "blob:mock-url";
}
if (typeof URL.revokeObjectURL !== "function") {
  URL.revokeObjectURL = () => {};
}
