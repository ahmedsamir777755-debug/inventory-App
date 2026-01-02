document.addEventListener("DOMContentLoaded", () => {
  const dashboard = document.getElementById("dashboard");

  dashboard.innerHTML = `
    <div style="padding:20px;background:#e3f2fd;border-radius:10px">
      <h3>✅ JavaScript is Working</h3>
      <p>If you see this box, app.js is connected correctly.</p>
    </div>
  `;
});
