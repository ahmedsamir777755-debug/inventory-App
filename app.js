alert("Inventory App Loaded");

document.getElementById("loadBtn").addEventListener("click", () => {
  const fileInput = document.getElementById("fileInput");
  if (!fileInput.files.length) {
    alert("Please choose an Excel file first");
    return;
  }

  const file = fileInput.files[0];
  const reader = new FileReader();

  reader.onload = (e) => {
    const data = new Uint8Array(e.target.result);
    const workbook = XLSX.read(data, { type: "array" });

    const dashboard = document.getElementById("dashboard");
    dashboard.innerHTML = `<h3>Sheets Found</h3><ul>` +
      workbook.SheetNames.map(s => `<li>${s}</li>`).join("") +
      `</ul>`;
  };

  reader.readAsArrayBuffer(file);
});
