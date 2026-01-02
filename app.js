alert("Inventory App Loaded");

function loadExcel() {
  const fileInput = document.getElementById("fileInput");
  const output = document.getElementById("output");

  if (!fileInput.files.length) {
    alert("اختار ملف Excel الأول");
    return;
  }

  const file = fileInput.files[0];
  const reader = new FileReader();

  reader.onload = function (e) {
    const data = new Uint8Array(e.target.result);
    const workbook = XLSX.read(data, { type: "array" });

    const sheetName = workbook.SheetNames[0];
    const sheet = workbook.Sheets[sheetName];

    const json = XLSX.utils.sheet_to_json(sheet, { header: 1 });

    let table = "<table>";

    json.forEach((row, index) => {
      table += "<tr>";
      row.forEach(cell => {
        if (index === 0) {
          table += `<th>${cell}</th>`;
        } else {
          table += `<td>${cell}</td>`;
        }
      });
      table += "</tr>";
    });

    table += "</table>";

    output.innerHTML = table;
  };

  reader.readAsArrayBuffer(file);
}
