const express = require("express");
const router = express.Router();
const {
  createSubmission,
  healthCheck,
} = require("../controllers/submissionsController");

router.get("/health", healthCheck);
router.post("/submissions", createSubmission);

module.exports = router;
