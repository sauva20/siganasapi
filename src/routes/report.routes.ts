import { Router } from "express";
import { authenticateToken } from "../middleware/auth";
import { getSummary, getPerLokasi, getPerPetani } from "../controllers/report.controller";

const router = Router();

router.get("/summary", authenticateToken, getSummary);
router.get("/per-lokasi", authenticateToken, getPerLokasi);
router.get("/per-petani", authenticateToken, getPerPetani);

export default router;
