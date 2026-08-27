import { Router } from "express";
import { traceBatch } from "../controllers/public.controller";

const router = Router();

// Endpoint ini tidak memerlukan autentikasi karena diakses publik via QR Code
router.get("/trace/:kode_batch", traceBatch);

export default router;
