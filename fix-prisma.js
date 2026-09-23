const fs = require('fs');
const path = require('path');

const enginesDir = path.join(__dirname, 'node_modules', '@prisma', 'engines');

if (fs.existsSync(enginesDir)) {
  const files = fs.readdirSync(enginesDir);
  let fixedCount = 0;
  
  files.forEach(file => {
    // Target all engine binaries (e.g., schema-engine-debian-openssl-1.1.x, query-engine-...)
    if (file.includes('engine') && !file.endsWith('.txt') && !file.endsWith('.json')) {
      try {
        const filePath = path.join(enginesDir, file);
        // 0o755 gives read, write, execute permissions to the owner, and read/execute to others
        fs.chmodSync(filePath, 0o755);
        console.log(`[SIGANAS] Fixed permissions for Prisma engine: ${file}`);
        fixedCount++;
      } catch (err) {
        console.error(`[SIGANAS] Failed to fix permissions for ${file}:`, err.message);
      }
    }
  });
  
  if (fixedCount === 0) {
    console.log('[SIGANAS] No Prisma engine binaries needed fixing.');
  }
} else {
  console.log('[SIGANAS] Prisma engines directory not found. Skipping permission fix.');
}
