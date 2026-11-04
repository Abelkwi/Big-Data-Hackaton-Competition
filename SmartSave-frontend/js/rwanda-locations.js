(() => {
  // Administrative hierarchy source: https://github.com/ngabovictor/Rwanda
  const provinceNames = {
    East: "Eastern Province",
    South: "Southern Province",
    West: "Western Province",
    North: "Northern Province",
    Kigali: "Kigali City",
  };
  const provinceOrder = ["East", "South", "West", "North", "Kigali"];

  function setOptions(select, entries, placeholder) {
    select.replaceChildren(new Option(placeholder, ""));
    entries.forEach(([value, label]) => {
      select.add(new Option(label, value));
    });
    select.disabled = entries.length === 0;
  }

  async function initializeAddress(address, data) {
    const province = address.querySelector('[data-location-level="province"]');
    const district = address.querySelector('[data-location-level="district"]');
    const sector = address.querySelector('[data-location-level="sector"]');
    const cell = address.querySelector('[data-location-level="cell"]');

    setOptions(
      province,
      provinceOrder.map(key => [provinceNames[key], provinceNames[key]]),
      "Select province"
    );
    setOptions(district, [], "Select district");
    setOptions(sector, [], "Select sector");
    setOptions(cell, [], "Select cell");

    province.addEventListener("change", () => {
      const key = provinceOrder.find(item => provinceNames[item] === province.value);
      setOptions(
        district,
        key ? Object.keys(data[key] || {}).sort().map(name => [name, name]) : [],
        "Select district"
      );
      setOptions(sector, [], "Select sector");
      setOptions(cell, [], "Select cell");
    });
    district.addEventListener("change", () => {
      const key = provinceOrder.find(item => provinceNames[item] === province.value);
      const sectors = key ? data[key]?.[district.value] : null;
      setOptions(
        sector,
        sectors ? Object.keys(sectors).sort().map(name => [name, name]) : [],
        "Select sector"
      );
      setOptions(cell, [], "Select cell");
    });
    sector.addEventListener("change", () => {
      const key = provinceOrder.find(item => provinceNames[item] === province.value);
      const cells = data[key]?.[district.value]?.[sector.value];
      setOptions(
        cell,
        cells ? Object.keys(cells).sort().map(name => [name, name]) : [],
        "Select cell"
      );
    });
  }

  document.addEventListener("DOMContentLoaded", async () => {
    const addresses = [...document.querySelectorAll("[data-rwanda-address]")];
    if (!addresses.length) return;

    try {
      const response = await fetch("data/rwanda-locations.json");
      if (!response.ok) throw new Error(`Location data request failed (${response.status}).`);
      const data = await response.json();
      await Promise.all(addresses.map(address => initializeAddress(address, data)));
    } catch (error) {
      addresses.forEach(address => {
        const status = address.querySelector("[data-location-error]");
        if (status) status.textContent = "Rwanda location choices could not be loaded. Please reload and try again.";
      });
      console.error("Could not load Rwanda administrative divisions.", error);
    }
  });
})();
