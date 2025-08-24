const form = document.getElementById("emailForm");
const result = document.getElementById("result");
const categoriaEl = document.getElementById("categoria");
const respostaEl = document.getElementById("resposta");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  result.classList.add("hidden");
  categoriaEl.textContent = "";
  respostaEl.textContent = "";

  const fd = new FormData(form);
  try {
    const resp = await fetch("/classificar", { method: "POST", body: fd });
    const data = await resp.json();
    if (!resp.ok || !data.ok) {
      throw new Error(data.error || "Erro ao classificar.");
    }
    categoriaEl.textContent = data.categoria;
    respostaEl.textContent = data.resposta;
    result.classList.remove("hidden");
  } catch (err) {
    categoriaEl.textContent = "Erro";
    respostaEl.textContent = err.message;
    result.classList.remove("hidden");
  }
});