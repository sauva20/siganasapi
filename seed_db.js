const { execSync } = require('child_process');

try {
  console.log("Seeding database...");
  execSync('npx ts-node seed.ts', {
    stdio: 'inherit',
    env: {
      ...process.env,
      DATABASE_URL: "mysql://u379683115_nanas_grading:Qisacantik2005@srv2257.hstgr.io:3306/u379683115_nanas_grading?connection_limit=3"
    }
  });
  console.log("Database seeded successfully!");
} catch (error) {
  console.error("Error seeding:", error);
}
