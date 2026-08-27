import { Router } from "express";
import { authenticateToken } from "../middleware/auth";
import { listUsers } from "../controllers/user.controller";

const router = Router();

router.get("/", authenticateToken, listUsers);

export default router;
