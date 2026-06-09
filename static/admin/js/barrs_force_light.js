// Força light mode no admin Barrs.
// O Alpine.js usa Alpine.$persist para salvar adminTheme no localStorage.
// Este script roda ANTES do Alpine inicializar e garante que o valor
// persistido seja sempre 'light', independente do OS ou sessão anterior.
(function () {
  try {
    localStorage.setItem('adminTheme', 'light');
  } catch (e) {}
})();
