// Ligação ao Supabase para preços reais.
// A URL e a chave "anon" são públicas por design (protegidas por RLS):
// a app só lê. A chave service_role NUNCA está aqui — fica no workflow de scraping.
window.SUPABASE = {
  url: "https://pieijihvcpcqzercvjhb.supabase.co",
  anonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBpZWlqaWh2Y3BjcXplcmN2amhiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNzY4NDYsImV4cCI6MjEwMjY1Mjg0Nn0.W9M-gupveDakCa3hfi5RGA8_fIR_-peqJYHYE1pWZIk",
};
