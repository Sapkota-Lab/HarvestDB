export function validateRecord(form) {
  const errors = {};
  const plotNumber = form.plot_number.trim();

  if (!plotNumber) {
    errors.plot_number = "Enter a plot number.";
  } else if (Array.from(plotNumber).length > 64) {
    errors.plot_number = "Plot number must be 64 characters or fewer.";
  }

  let dynamicData;
  try {
    dynamicData = JSON.parse(form.dynamic_data);
    if (dynamicData === null || Array.isArray(dynamicData) || typeof dynamicData !== "object") {
      errors.dynamic_data = 'Enter a JSON object, such as {"weight": 12.5}. Use {} for no measurements.';
    }
  } catch {
    errors.dynamic_data = "Enter valid JSON with double quotes around field names and text values.";
  }

  return {
    errors,
    payload: Object.keys(errors).length === 0
      ? { plot_number: plotNumber, dynamic_data: dynamicData }
      : null
  };
}
