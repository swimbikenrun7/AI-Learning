(function () {
  const dateInput = document.getElementById("date-input");
  const datePicker = document.getElementById("date-picker");
  datePicker.max = new Date().toISOString().slice(0, 10);

  dateInput.addEventListener("input", () => {
    const digits = dateInput.value.replace(/\D/g, "").slice(0, 8);
    let formatted = digits.slice(0, 2);
    if (digits.length > 2) formatted += "/" + digits.slice(2, 4);
    if (digits.length > 4) formatted += "/" + digits.slice(4, 8);
    dateInput.value = formatted;
  });

  datePicker.addEventListener("change", () => {
    if (!datePicker.value) return;
    const [year, month, day] = datePicker.value.split("-");
    dateInput.value = `${month}/${day}/${year}`;
  });
})();
