import express from "express";
import cors from "cors";
import helmet from "helmet";
import morgan from "morgan";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(cors());
app.use(helmet());
app.use(morgan("dev"));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

import authRoutes from "./routes/auth.routes";
import userRoutes from "./routes/user.routes";
import kebunRoutes from "./routes/kebun.routes";
import batchRoutes from "./routes/batch.routes";
import reportRoutes from "./routes/report.routes";
import yoloRoutes from "./routes/yolo.routes";
import publicRoutes from "./routes/public.routes";

// API Routes
app.use("/api/v1/auth", authRoutes);
app.use("/api/v1/users", userRoutes);
app.use("/api/v1/kebun", kebunRoutes);
app.use("/api/v1/batches", batchRoutes);
app.use("/api/v1/reports", reportRoutes);
app.use("/api/v1/yolo", yoloRoutes);
app.use("/public", publicRoutes);

// Serve uploaded static files
app.use('/static', express.static('static'));

// Health check
app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

app.get("/", (req, res) => {
  res.json({
    app: "Nanas Grading API (Node.js)",
    version: "1.0.0",
    status: "running"
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Server ready at: http://localhost:${PORT}`);
});
