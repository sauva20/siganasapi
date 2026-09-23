import { Router } from "express";
import { authenticateToken, requireRole } from "../middleware/auth";
import { createBatch, listBatches, getBatch, sealBatch } from "../controllers/batch.controller";

const router = Router();

router.post("/", authenticateToken, requireRole(["petani", "dinas_pertanian"]), createBatch);
router.get("/", authenticateToken, listBatches);
router.get("/:id", authenticateToken, getBatch);
router.post("/:id/seal", authenticateToken, requireRole(["petani", "dinas_pertanian", "pengepul"]), sealBatch);

export default router;
