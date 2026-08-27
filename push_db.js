const { execSync } = require('child_process');

try {
  console.log("Pushing database schema...");
  execSync('npx prisma db push --accept-data-loss', {
    stdio: 'inherit',
    env: {
      ...process.env,
      DATABASE_URL: "mysql://u379683115_nanas_grading:Qisacantik2005@srv2257.hstgr.io:3306/u379683115_nanas_grading?connection_limit=3"
    }
  });
  console.log("Database schema pushed successfully!");
} catch (error) {
  console.error("Error pushing schema:", error);
}
