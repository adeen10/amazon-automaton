import { useMemo, useState } from "react";

/* ---------- helpers ---------- */
const COUNTRY_OPTIONS = ["US", "UK", "CAN", "DE", "AUS", "UAE"];
const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

// URL validation helper
const isValidUrl = (url) => {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname.toLowerCase().includes('amazon.com');
  } catch {
    return false;
  }
};

// Validation helper
const validateStep1 = (brands) => {
  const errors = [];
  
  brands.forEach((brand, brandIndex) => {
    if (!brand.name.trim()) {
      errors.push(`Brand ${brandIndex + 1}: Brand name is required`);
    }
    
    brand.countries.forEach((country, countryIndex) => {
      if (!country.name) {
        errors.push(`Brand ${brandIndex + 1}, Country ${countryIndex + 1}: Country is required`);
      }
      if (!country.count || country.count < 1) {
        errors.push(`Brand ${brandIndex + 1}, Country ${countryIndex + 1}: Product count must be at least 1`);
      }
    });
  });
  
  return errors;
};

const validateStep2 = (detail) => {
  const errors = [];
  
  detail.forEach((brand, brandIndex) => {
    brand.countries.forEach((country, countryIndex) => {
      country.products.forEach((product, productIndex) => {
        if (!product.productname.trim()) {
          errors.push(`Brand "${brand.brand}", Country "${country.name}", Product ${productIndex + 1}: Product name is required`);
        }
        if (!product.url.trim()) {
          errors.push(`Brand "${brand.brand}", Country "${country.name}", Product ${productIndex + 1}: Product URL is required`);
        } else if (!isValidUrl(product.url)) {
          errors.push(`Brand "${brand.brand}", Country "${country.name}", Product ${productIndex + 1}: Product URL must be a valid Amazon URL`);
        }
        if (!product.keyword.trim()) {
          errors.push(`Brand "${brand.brand}", Country "${country.name}", Product ${productIndex + 1}: Keyword is required`);
        }
        if (!product.categoryUrl.trim()) {
          errors.push(`Brand "${brand.brand}", Country "${country.name}", Product ${productIndex + 1}: Category URL is required`);
        } else if (!isValidUrl(product.categoryUrl)) {
          errors.push(`Brand "${brand.brand}", Country "${country.name}", Product ${productIndex + 1}: Category URL must be a valid Amazon URL`);
        }
      });
    });
  });
  
  return errors;
};

/* ---------- app ---------- */
export default function App() {
  const [step, setStep] = useState(1);
  const [showErrors, setShowErrors] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

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
    // Validate step 1 data
    const step1Errors = validateStep1(brands);
    if (step1Errors.length > 0) {
      const errorMessage = "❌ Please fix the following errors:\n\n" + step1Errors.join('\n');
      alert(errorMessage);
      return;
    }

    const built = brands.map((b) => ({
      brand: b.name,
      countries: b.countries.map((c) => ({
        name: c.name,
        products: Array.from({ length: c.count }, () => ({
          productname: "",
          url: "",
          keyword: "",
          categoryUrl: "",
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
    // Validate step 2 data
    const step2Errors = validateStep2(detail);
    if (step2Errors.length > 0) {
      const errorMessage = "❌ Please fix the following errors:\n\n" + step2Errors.join('\n');
      alert(errorMessage);
      return;
    }

    // Set loading state
    setIsSubmitting(true);

    // Shape payload to match backend expectations
    const payload = { 
      brands: detail.map(brand => ({
        brand: brand.brand,
        countries: brand.countries.map(country => ({
          name: country.name,
          products: country.products.map(product => ({
            productname: product.productname,
            url: product.url,
            keyword: product.keyword,
            categoryUrl: product.categoryUrl
          }))
        }))
      }))
    };

    try {
      console.log("Submitting payload:", payload);
      
      const response = await fetch("http://localhost:4000/api/submissions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const result = await response.json();
      
      if (response.ok) {
        console.log("SUBMIT SUCCESS", result);
        
        // Show appropriate message based on response
        if (result.message && result.message.includes("queue")) {
          alert("✅ " + result.message);
        } else {
          alert("✅ Submitted successfully! The scraper is now running in the background.");
        }
        
        // Reset to step 1 after successful submission
        setStep(1);
        setBrands([{ name: "", countries: [{ name: "US", count: 1 }] }]);
        setDetail([]);
        setSectionIndex(0);
      } else {
        console.error("SUBMIT ERROR", result);
        alert(`❌ Submission failed: ${result.error || 'Unknown error'}`);
      }
    } catch (e) {
      console.error("SUBMIT EXCEPTION", e);
      alert(`❌ Failed to submit: ${e.message}`);
    } finally {
      // Clear loading state
      setIsSubmitting(false);
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
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">Product Intake</h1>
          <div className="text-sm text-slate-400">
            Step {step} of 2
          </div>
        </div>

        {step === 1 && (
          <div className="space-y-6">
            <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <div className="text-blue-400 text-lg">💡</div>
                <div>
                  <h3 className="font-semibold text-blue-300 mb-2">Step 1: Setup Brands & Countries</h3>
                  <p className="text-sm text-slate-300">
                    Add your brands and specify which countries you want to analyze. For each country, 
                    set the number of products you want to process (1-10).
                  </p>
                </div>
              </div>
            </div>
            {brands.map((b, bi) => (
              <div
                key={bi}
                className="bg-slate-800/50 rounded-xl p-6 border border-slate-700"
              >
                <div className="flex gap-3 items-end">
                  <div className="flex-1">
                    <label className="block text-sm mb-1">Brand</label>
                    <input
                      className={`w-full rounded-lg bg-slate-800 border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                        b.name && !b.name.trim() 
                          ? 'border-red-500 focus:ring-red-500' 
                          : b.name && b.name.trim()
                          ? 'border-green-500 focus:ring-green-500'
                          : 'border-slate-700'
                      }`}
                      placeholder="e.g. Big Wipes"
                      value={b.name}
                      onChange={(e) => updateBrandName(bi, e.target.value)}
                    />
                    {b.name && !b.name.trim() && (
                      <div className="text-xs text-red-400 mt-1">
                        ⚠️ Brand name cannot be empty
                      </div>
                    )}
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
            <div className="bg-green-900/20 border border-green-700/50 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <div className="text-green-400 text-lg">📝</div>
                <div>
                  <h3 className="font-semibold text-green-300 mb-2">Step 2: Product Details</h3>
                  <p className="text-sm text-slate-300">
                    Fill in the details for each product. Make sure all URLs are valid Amazon URLs 
                    (must contain "amazon.com"). All fields are required.
                  </p>
                </div>
              </div>
            </div>
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
                      className={`w-full rounded-lg bg-slate-900 border px-3 py-2 focus:ring-2 focus:ring-blue-500 ${
                        p.productname && !p.productname.trim() 
                          ? 'border-red-500 focus:ring-red-500' 
                          : p.productname && p.productname.trim()
                          ? 'border-green-500 focus:ring-green-500'
                          : 'border-slate-700'
                      }`}
                      value={p.productname}
                      onChange={(e) => updateProduct(pi, "productname", e.target.value)}
                      placeholder="cricket bat"
                    />
                    {p.productname && !p.productname.trim() && (
                      <div className="text-xs text-red-400 mt-1">
                        ⚠️ Product name cannot be empty
                      </div>
                    )}
                  </div>

                  <div className="md:col-span-5">
                    <label className="block text-xs mb-1">
                      Amazon Product Listing URL
                    </label>
                    <input
                      className={`w-full rounded-lg bg-slate-900 border px-3 py-2 focus:ring-2 focus:ring-blue-500 ${
                        p.url && !isValidUrl(p.url) 
                          ? 'border-red-500 focus:ring-red-500' 
                          : p.url && isValidUrl(p.url)
                          ? 'border-green-500 focus:ring-green-500'
                          : 'border-slate-700'
                      }`}
                      value={p.url}
                      onChange={(e) => updateProduct(pi, "url", e.target.value)}
                      placeholder="https://www.amazon.com/..."
                    />
                    {p.url && !isValidUrl(p.url) && (
                      <div className="text-xs text-red-400 mt-1">
                        ⚠️ Please enter a valid Amazon URL
                      </div>
                    )}
                    {p.url && isValidUrl(p.url) && (
                      <div className="text-xs text-green-400 mt-1">
                        ✅ Valid Amazon URL
                      </div>
                    )}
                  </div>

                  <div className="md:col-span-3">
                    <label className="block text-xs mb-1">Keyword</label>
                    <input
                      className={`w-full rounded-lg bg-slate-900 border px-3 py-2 focus:ring-2 focus:ring-blue-500 ${
                        p.keyword && !p.keyword.trim() 
                          ? 'border-red-500 focus:ring-red-500' 
                          : p.keyword && p.keyword.trim()
                          ? 'border-green-500 focus:ring-green-500'
                          : 'border-slate-700'
                      }`}
                      value={p.keyword}
                      onChange={(e) =>
                        updateProduct(pi, "keyword", e.target.value)
                      }
                      placeholder="e.g. hand wipes"
                    />
                    {p.keyword && !p.keyword.trim() && (
                      <div className="text-xs text-red-400 mt-1">
                        ⚠️ Keyword cannot be empty
                      </div>
                    )}
                  </div>

                  <div className="md:col-span-3">
                    <label className="block text-xs mb-1">Category URL</label>
                    <input
                      className={`w-full rounded-lg bg-slate-900 border px-3 py-2 focus:ring-2 focus:ring-blue-500 ${
                        p.categoryUrl && !isValidUrl(p.categoryUrl) 
                          ? 'border-red-500 focus:ring-red-500' 
                          : p.categoryUrl && isValidUrl(p.categoryUrl)
                          ? 'border-green-500 focus:ring-green-500'
                          : 'border-slate-700'
                      }`}
                      value={p.categoryUrl}
                      onChange={(e) =>
                        updateProduct(pi, "categoryUrl", e.target.value)
                      }
                      placeholder="https://www.amazon.com/..."
                    />
                    {p.categoryUrl && !isValidUrl(p.categoryUrl) && (
                      <div className="text-xs text-red-400 mt-1">
                        ⚠️ Please enter a valid Amazon URL
                      </div>
                    )}
                    {p.categoryUrl && isValidUrl(p.categoryUrl) && (
                      <div className="text-xs text-green-400 mt-1">
                        ✅ Valid Amazon URL
                      </div>
                    )}
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
                  disabled={isSubmitting}
                  className={`ml-auto px-4 py-2 rounded-lg ${
                    isSubmitting
                      ? "bg-green-400 opacity-50 cursor-not-allowed"
                      : "bg-green-600 hover:bg-green-700"
                  }`}
                >
                  {isSubmitting ? "Submitting..." : "Submit all"}
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
