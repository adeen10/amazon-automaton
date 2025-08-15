const {
  HYPER,
  getNextRowFromA,
  writeRowsAt,
  getSheetMeta,
  insertRowBelowReq,
  copyFormatReq,
  batchUpdate,
} = require("../sheets-helpers");
const { spawn } = require('child_process');
const path = require('path');

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

    // Validate and prepare payload for scraper
    const scraperPayload = {
      brands: brands.map(brand => ({
        brand: brand.brand || brand.name || "",
        countries: (brand.countries || []).map(country => ({
          name: normalizeCountry(country.name),
          products: (country.products || []).map(product => ({
            productname: product.productname || product.name || "",
            url: product.url || "",
            keyword: product.keyword || "",
            categoryUrl: product.categoryUrl || ""
          }))
        }))
      }))
    };

    // Filter out invalid countries
    scraperPayload.brands = scraperPayload.brands.map(brand => ({
      ...brand,
      countries: brand.countries.filter(country => 
        VALID_COUNTRIES.includes(country.name)
      )
    })).filter(brand => brand.countries.length > 0);

    if (scraperPayload.brands.length === 0) {
      return res.status(400).json({ error: "No valid countries found" });
    }

    console.log("Prepared scraper payload:", JSON.stringify(scraperPayload, null, 2));

    // Start the scraper process in the background
    const scraperScriptPath = path.join(__dirname, '../scraper/run_scraper.py');
    const pythonProcess = spawn('python', [scraperScriptPath], {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: path.dirname(scraperScriptPath),
      detached: true // Run in background
    });

    // Send payload to Python process
    pythonProcess.stdin.write(JSON.stringify(scraperPayload));
    pythonProcess.stdin.end();

    // Detach the process so it runs independently
    pythonProcess.unref();

    // Respond immediately to frontend
    console.log('Scraper started successfully in background');
    res.json({ 
      ok: true, 
      message: 'Scraper started successfully in the background',
      payload: scraperPayload
    });

    // Handle process events for logging (but don't wait for response)
    pythonProcess.stdout.on('data', (data) => {
      const message = data.toString();
      console.log('Scraper output:', message);
    });

    pythonProcess.stderr.on('data', (data) => {
      const errorMessage = data.toString();
      console.error('Scraper error:', errorMessage);
    });

    pythonProcess.on('close', (code) => {
      console.log(`Scraper process completed with code: ${code}`);
    });

    pythonProcess.on('error', (error) => {
      console.error('Failed to start scraper:', error);
    });

  } catch (e) {
    console.error("Submission processing failed:", e);
    return res.status(500).json({ error: "Submission processing failed", details: e.message });
  }
};

exports.healthCheck = (_req, res) => res.json({ ok: true });
