// Ligação ao Supabase para preços reais.
// O workflow de deploy (.github/workflows/pages.yml) preenche isto a partir
// dos segredos do repositório. Se ficar vazio, a app usa os preços curados.
window.SUPABASE = {
  url: "",      // ex.: "https://xyzcompany.supabase.co"
  anonKey: "",  // chave "anon/public" (é segura para estar no cliente)
};
