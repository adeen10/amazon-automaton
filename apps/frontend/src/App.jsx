import { useMemo, useState } from "react";

/* ---------- helpers ---------- */
const COUNTRY_OPTIONS = ["US", "UK", "CAN", "DE", "AUS", "UAE"];
const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

/* ---------- app ---------- */
export default function App() {
  const [step, setStep] = useState(1);

  // Step 1 data model
  const [brands, setBrands] = useState([
    { name: "", countries: [{ name: "US", count: 1 }] },
  ]);

  // Step 2 data model (built from step 1)
  const [detail, setDetail] = useState([]); // [{brand, countries:[{name, products:[{url, keyword}]}]}]
  const sections = useMemo(
    () =>
      detail.flatMap((b, bi) =>
        b.countries.map((c, ci) => ({
          bi,
          ci,
          label: `${b.brand || "Brand"} • ${c.name}`,
        }))
      ),
    [detail]
  );
  const [sectionIndex, setSectionIndex] = useState(0);
  const totalSections = sections.length || 1;
  const progressPct = Math.round((sectionIndex / totalSections) * 100);

  /* --------- STEP 1 actions --------- */
  const addBrand = () =>
    setBrands((prev) => [
      ...prev,
      { name: "", countries: [{ name: "US", count: 1 }] },
    ]);

  const removeBrand = (bi) =>
    setBrands((prev) =>
      prev.length === 1 ? prev : prev.filter((_, i) => i !== bi)
    );

  const updateBrandName = (bi, v) =>
    setBrands((prev) => {
      const next = [...prev];
      next[bi].name = v;
      return next;
    });

  const addCountry = (bi) =>
    setBrands((prev) => {
      const next = prev.map((b) => ({
        ...b,
        countries: b.countries.map((c) => ({ ...c })),
      }));
      next[bi].countries.push({ name: "US", count: 1 });
      return next;
    });

  const removeCountry = (bi, ci) =>
    setBrands((prev) => {
      const next = prev.map((b) => ({
        ...b,
        countries: b.countries.map((c) => ({ ...c })),
      }));
      if (next[bi].countries.length > 1) next[bi].countries.splice(ci, 1);
      return next;
    });

  const updateCountryName = (bi, ci, v) =>
    setBrands((prev) => {
      const next = prev.map((b) => ({
        ...b,
        countries: b.countries.map((c) => ({ ...c })),
      }));
      next[bi].countries[ci].name = v;
      return next;
    });

  const updateCount = (bi, ci, v) =>
    setBrands((prev) => {
      const next = prev.map((b) => ({
        ...b,
        countries: b.countries.map((c) => ({ ...c })),
      }));
      next[bi].countries[ci].count = clamp(parseInt(v || "1", 10) || 1, 1, 10);
      return next;
    });

  const goStep2 = () => {
    const built = brands.map((b) => ({
      brand: b.name,
      countries: b.countries.map((c) => ({
        name: c.name,
        products: Array.from({ length: c.count }, () => ({
          productname: "",
          url: "",
          keyword: "",
          categoryUrl: "", // NEW
        })),
      })),
    }));
    setDetail(built);
    setSectionIndex(0);
    setStep(2);
  };

  /* --------- STEP 2 actions --------- */
  const cur = sections[sectionIndex] || { bi: 0, ci: 0 };
  const currentBrand = detail[cur.bi]?.brand || "";
  const currentCountry = detail[cur.bi]?.countries?.[cur.ci];

  const updateProduct = (pi, field, value) =>
    setDetail((prev) => {
      const next = prev.map((b) => ({
        ...b,
        countries: b.countries.map((c) => ({
          ...c,
          products: c.products.map((p) => ({ ...p })),
        })),
      }));
      next[cur.bi].countries[cur.ci].products[pi][field] = value;
      return next;
    });

  const addProduct = () =>
    setDetail((prev) => {
      const next = prev.map((b) => ({
        ...b,
        countries: b.countries.map((c) => ({
          ...c,
          products: c.products.map((p) => ({ ...p })), // deep clone products
        })),
      }));
      const arr = next[cur.bi].countries[cur.ci].products;
      if (arr.length < 10)
        arr.push({ productname: "", url: "", keyword: "", categoryUrl: "" });
      return next;
    });

  const removeProduct = (pi) =>
    setDetail((prev) => {
      const next = prev.map((b) => ({
        ...b,
        countries: b.countries.map((c) => ({
          ...c,
          products: c.products.map((p) => ({ ...p })),
        })),
      }));
      const arr = next[cur.bi].countries[cur.ci].products;
      if (arr.length > 1) arr.splice(pi, 1);
      return next;
    });

  const prevSection = () =>
    setSectionIndex((i) => clamp(i - 1, 0, totalSections - 1));
  const nextSection = () =>
    setSectionIndex((i) => clamp(i + 1, 0, totalSections - 1));

  const handleSubmit = async () => {
    // shape payload
    const payload = { brands: detail };
    try {
      // TODO: replace with your backend URL
      await fetch("http://localhost:4000/api/submissions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      console.log("SUBMIT", payload);
      alert("Submitted ✅");
    } catch (e) {
      alert("Failed to submit");
    }
  };

  /* ---------- UI ---------- */
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      {/* progress bar (only step 2 uses it) */}
      {step === 2 && (
        <div className="h-1 w-full bg-slate-800">
          <div
            className="h-1 bg-blue-500 transition-all"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      )}

      <div className="max-w-5xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Product Intake</h1>

        {step === 1 && (
          <div className="space-y-6">
            {brands.map((b, bi) => (
              <div
                key={bi}
                className="bg-slate-800/50 rounded-xl p-6 border border-slate-700"
              >
                <div className="flex gap-3 items-end">
                  <div className="flex-1">
                    <label className="block text-sm mb-1">Brand</label>
                    <input
                      className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g. Big Wipes"
                      value={b.name}
                      onChange={(e) => updateBrandName(bi, e.target.value)}
                    />
                  </div>
                  {brands.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeBrand(bi)}
                      className="px-3 py-2 rounded-lg bg-red-600 hover:bg-red-700"
                    >
                      Remove brand
                    </button>
                  )}
                </div>

                <div className="mt-5 space-y-4">
                  <div className="text-sm font-medium opacity-80">
                    Countries & product counts
                  </div>
                  {b.countries.map((c, ci) => (
                    <div
                      key={ci}
                      className="grid grid-cols-1 md:grid-cols-3 gap-3 bg-slate-800/60 p-4 rounded-lg border border-slate-700"
                    >
                      <div>
                        <label className="block text-xs mb-1">Country</label>
                        <select
                          className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 focus:ring-2 focus:ring-blue-500"
                          value={c.name}
                          onChange={(e) =>
                            updateCountryName(bi, ci, e.target.value)
                          }
                        >
                          {COUNTRY_OPTIONS.map((opt) => (
                            <option key={opt} value={opt}>
                              {opt}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs mb-1">
                          Number of products (1–10)
                        </label>
                        <input
                          type="number"
                          min={1}
                          max={10}
                          className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 focus:ring-2 focus:ring-blue-500"
                          value={c.count}
                          onChange={(e) => updateCount(bi, ci, e.target.value)}
                        />
                      </div>
                      <div className="flex items-end gap-2">
                        <button
                          type="button"
                          onClick={() => removeCountry(bi, ci)}
                          className="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600"
                        >
                          Remove country
                        </button>
                      </div>
                    </div>
                  ))}

                  <button
                    type="button"
                    onClick={() => addCountry(bi)}
                    className="px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700"
                  >
                    + Add country
                  </button>
                </div>
              </div>
            ))}

            <div className="flex gap-3">
              <button
                type="button"
                onClick={addBrand}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700"
              >
                + Add brand
              </button>

              <button
                type="button"
                onClick={goStep2}
                className="ml-auto px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700"
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {step === 2 && currentCountry && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm opacity-70">Section</div>
                <div className="text-xl font-semibold">
                  {sections[sectionIndex]?.label}
                </div>
              </div>
              <div className="text-sm opacity-70">
                {sectionIndex + 1} / {totalSections}
              </div>
            </div>

            {/* products list for current brand+country */}
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 space-y-3">
              {currentCountry.products.map((p, pi) => (
                <div
                  key={pi}
                  className="grid grid-cols-1 md:grid-cols-12 gap-3 bg-slate-900/60 p-4 rounded-lg border border-slate-700"
                >
                  <div className="md:col-span-5">
                    <label className="block text-xs mb-1">
                      Product name
                    </label>
                    <input
                      className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 focus:ring-2 focus:ring-blue-500"
                      value={p.productname}
                      onChange={(e) => updateProduct(pi, "productname", e.target.value)}
                      placeholder="cricket bat"
                    />
                  </div>

                  <div className="md:col-span-5">
                    <label className="block text-xs mb-1">
                      Amazon Product Listing URL
                    </label>
                    <input
                      className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 focus:ring-2 focus:ring-blue-500"
                      value={p.url}
                      onChange={(e) => updateProduct(pi, "url", e.target.value)}
                      placeholder="https://www.amazon.com/..."
                    />
                  </div>

                  <div className="md:col-span-3">
                    <label className="block text-xs mb-1">Keyword</label>
                    <input
                      className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 focus:ring-2 focus:ring-blue-500"
                      value={p.keyword}
                      onChange={(e) =>
                        updateProduct(pi, "keyword", e.target.value)
                      }
                      placeholder="e.g. hand wipes"
                    />
                  </div>

                  <div className="md:col-span-3">
                    <label className="block text-xs mb-1">Category URL</label>
                    <input
                      className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 focus:ring-2 focus:ring-blue-500"
                      value={p.categoryUrl}
                      onChange={(e) =>
                        updateProduct(pi, "categoryUrl", e.target.value)
                      }
                      placeholder="https://www.amazon.com/..."
                    />
                  </div>

                  <div className="md:col-span-1 flex items-end">
                    <button
                      type="button"
                      onClick={() => removeProduct(pi)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={addProduct}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700"
                >
                  + Add product
                </button>
              </div>
            </div>

            {/* nav + submit */}
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600"
              >
                ← Back to setup
              </button>

              <button
                type="button"
                onClick={prevSection}
                disabled={sectionIndex === 0}
                className={`px-4 py-2 rounded-lg ${
                  sectionIndex === 0
                    ? "bg-slate-700 opacity-50 cursor-not-allowed"
                    : "bg-slate-700 hover:bg-slate-600"
                }`}
              >
                ← Prev
              </button>

              {sectionIndex < totalSections - 1 ? (
                <button
                  type="button"
                  onClick={nextSection}
                  className="ml-auto px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700"
                >
                  Next →
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleSubmit}
                  className="ml-auto px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700"
                >
                  Submit all
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
