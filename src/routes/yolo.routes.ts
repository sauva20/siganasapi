import { Router } from "express";
import multer from "multer";
import path from "path";
import fs from "fs";
import { authenticateToken, requireRole } from "../middleware/auth";
import { scanPineapple } from "../controllers/yolo.controller";

const router = Router();

// Configure multer for file uploads
const uploadDir = path.join(__dirname, "../../static/uploads");
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1e9);
    cb(null, "nanas-" + uniqueSuffix + path.extname(file.originalname));
  },
});

const fileFilter = (req: any, file: any, cb: any) => {
  const allowedExtensions = [".jpg", ".jpeg", ".png", ".webp"];
  const ext = path.extname(file.originalname).toLowerCase();
  if (allowedExtensions.includes(ext)) {
    cb(null, true);
  } else {
    cb(new Error("Format file tidak didukung"), false);
  }
};

const upload = multer({ storage, fileFilter, limits: { fileSize: 10 * 1024 * 1024 } }); // 10 MB

router.post("/scan", authenticateToken, requireRole(["petani", "pengepul", "dinas_pertanian"]), upload.single("file"), scanPineapple);

export default router;
