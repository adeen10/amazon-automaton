const {
  HYPER,
  getNextRowFromA,
  writeRowsAt,
  getSheetMeta,
  insertRowBelowReq,
  copyFormatReq,
  batchUpdate,
} = require("../sheets-helpers");

const VALID_COUNTRIES = ["US", "UK", "CAN", "AUS", "DE", "UAE"];

const normalizeCountry = (v = "") => {
  const x = String(v).trim().toUpperCase();
  if (x === "AU") return "AUS";
  return x;
};

exports.createSubmission = async (req, res) => {
  console.dir(req.body, { depth: null, maxArrayLength: null });

  try {
    const { brands } = req.body || {};
    if (!Array.isArray(brands) || !brands.length) {
      return res.status(400).json({ error: "No brands provided" });
    }

    // Build country -> items
    const map = new Map();
    for (const b of brands) {
      for (const c of b.countries || []) {
        const country = normalizeCountry(c.name);
        if (!VALID_COUNTRIES.includes(country)) {
          console.warn("Skipping invalid/unknown country:", c.name);
          continue;
        }
        const list = map.get(country) || [];
        for (const p of c.products || []) {
          list.push({
            categoryUrl: p.categoryUrl || "",
            productUrl: p.url || "",
            productName: p.productname || p.name || "Product",
          });
        }
        map.set(country, list);
      }
    }

    // Order by sheet tab sequence
    const countries = Array.from(map.keys()).sort(
      (a, b) => VALID_COUNTRIES.indexOf(a) - VALID_COUNTRIES.indexOf(b)
    );

    console.log("Will write countries:", countries);

    const results = [];
    for (const country of countries) {
      if (!country) continue;
      const items = map.get(country);
      if (!items || !items.length) continue;

      const startRow = await getNextRowFromA(country);
      const rows = items.map((it, i) => [
        startRow - 3 + 1 + i,
        HYPER(it.categoryUrl, "link"),
        HYPER(it.productUrl, it.productName),
      ]);

      await writeRowsAt(country, startRow, rows);
      const { sheetId, columnCount } = await getSheetMeta(country);
      const lastRow1 = startRow + rows.length - 1;
      const lastRow0 = lastRow1 - 1;

      await batchUpdate([
        insertRowBelowReq(sheetId, lastRow0),
        copyFormatReq(sheetId, lastRow0, lastRow0 + 1, columnCount),
      ]);

      results.push({
        country,
        added: rows.length,
        fromNo: rows[0][0],
        toNo: rows[rows.length - 1][0],
      });
    }

    return res.json({ ok: true, results });
  } catch (e) {
    console.error("Sheets write failed:", e?.response?.data || e);
    return res.status(500).json({ error: "Sheets write failed" });
  }
};

exports.healthCheck = (_req, res) => res.json({ ok: true });
