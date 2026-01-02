window.loadFile = function () {
  const fileInput = document.getElementById("fileInput");
  const output = document.getElementById("output");

  if (!fileInput.files.length) {
    alert("Please choose an Excel file first");
    return;
  }

  const file = fileInput.files[0];
  const reader = new FileReader();

  reader.onload = function (e) {
    try {
      const data = new Uint8Array(e.target.result);
      const workbook = XLSX.read(data, { type: "array" });

      console.log("Sheets:", workbook.SheetNames);

      // خُد أول شيت (عشان نضمن إنه يشتغل)
      const sheetName = workbook.SheetNames[0];
      const sheet = workbook.Sheets[sheetName];

      const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 });

      if (rows.length === 0) {
        output.innerHTML = "<b>No data found in sheet</b>";
        return;
      }

      let html = "<table border='1' cellpadding='5'><tr>";

      // Headers
      rows[0].forEach(h => {
        html += `<th>${h ?? ""}</th>`;
      });
      html += "</tr>";

      // Data
      for (let i = 1; i < rows.length; i++) {
        html += "<tr>";
        rows[i].forEach(cell => {
          html += `<td>${cell ?? ""}</td>`;
        });
        html += "</tr>";
      }

      html += "</table>";
      output.innerHTML = html;

    } catch (err) {
      console.error(err);
      alert("Error reading file, check console");
    }
  };

  reader.readAsArrayBuffer(file);
};

console.log("App ready");
