import { Router } from "express";
import { authenticateToken, requireRole } from "../middleware/auth";
import { createKebun, listKebun, getKebun, updateKebun, deactivateKebun } from "../controllers/kebun.controller";

const router = Router();

router.post("/", authenticateToken, requireRole(["dinas_pertanian"]), createKebun);
router.get("/", authenticateToken, listKebun);
router.get("/:id", authenticateToken, getKebun);
router.patch("/:id", authenticateToken, requireRole(["dinas_pertanian"]), updateKebun);
router.delete("/:id", authenticateToken, requireRole(["dinas_pertanian"]), deactivateKebun);

export default router;
