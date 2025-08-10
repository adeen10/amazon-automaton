require("dotenv").config();
const express = require("express");
const cors = require("cors");

const submissionsRoutes = require("./routes/submissions");

const app = express();
app.use(cors());
app.use(express.json({ limit: "4mb" }));

app.use("/api", submissionsRoutes);

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
