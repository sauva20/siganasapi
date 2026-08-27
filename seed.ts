import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log("Memulai pembuatan akun admin...");
  const password_hash = await bcrypt.hash("admin123", 10);
  
  const user = await prisma.user.upsert({
    where: { username: "dinas_admin" },
    update: {},
    create: {
      username: "dinas_admin",
      password_hash: password_hash,
      nama_lengkap: "Admin Dinas",
      role: "dinas",
      no_hp: "08123456789"
    }
  });

  console.log("Akun berhasil dibuat!");
  console.log(user);
}

main()
  .catch((e) => {
    console.error("Terjadi kesalahan:", e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
