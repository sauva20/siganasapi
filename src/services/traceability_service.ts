import { prisma } from "../db/prisma";
import { GENESIS_HASH, buildBlockData, computeHash } from "./blockchain_hash";
import { BatchPanen, Kebun, User } from "@prisma/client";

export const syncBlock = async (batch: BatchPanen) => {
  const kebun = await prisma.kebun.findUnique({ where: { id: batch.kebun_id } });
  if (!kebun) throw new Error("Kebun not found");

  const petani = await prisma.user.findUnique({ where: { id: kebun.petani_id } });
  if (!petani) throw new Error("Petani not found");

  const blockDataObj = buildBlockData(
    batch.id,
    batch.kode_batch,
    kebun.id,
    petani.id,
    petani.nama_lengkap,
    kebun.nama_kebun,
    kebun.latitude,
    kebun.longitude,
    batch.tanggal_panen,
    kebun.varietas_nanas || "Simadu",
    kebun.jenis_pupuk,
    batch.total_buah,
    batch.jumlah_grade_a,
    batch.jumlah_grade_b,
    batch.jumlah_grade_c,
    batch.jumlah_reject,
    batch.total_berat_kg
  );

  const blockDataString = JSON.stringify(blockDataObj);

  const existingBlock = await prisma.traceabilityBlockchain.findUnique({
    where: { batch_id: batch.id },
  });

  if (existingBlock) {
    const newHash = computeHash(blockDataObj, existingBlock.previous_hash);
    const updatedBlock = await prisma.traceabilityBlockchain.update({
      where: { id: existingBlock.id },
      data: {
        block_data: blockDataString,
        block_hash: newHash,
        is_valid: true,
      },
    });
    return updatedBlock;
  }

  const lastBlock = await prisma.traceabilityBlockchain.findFirst({
    orderBy: { block_index: "desc" },
  });

  const blockIndex = lastBlock ? lastBlock.block_index + 1 : 0;
  const previousHash = lastBlock ? lastBlock.block_hash : GENESIS_HASH;
  const blockHash = computeHash(blockDataObj, previousHash);

  const newBlock = await prisma.traceabilityBlockchain.create({
    data: {
      batch_id: batch.id,
      block_data: blockDataString,
      block_hash: blockHash,
      previous_hash: previousHash,
      block_index: blockIndex,
    },
  });

  return newBlock;
};

export const verifyBlock = async (batchId: number) => {
  const block = await prisma.traceabilityBlockchain.findUnique({
    where: { batch_id: batchId },
  });

  if (!block) {
    return { found: false, is_valid: null, detail: "Block tidak ditemukan untuk batch ini." };
  }

  const blockDataObj = JSON.parse(block.block_data);
  const recomputedHash = computeHash(blockDataObj, block.previous_hash);
  const isValid = recomputedHash === block.block_hash;

  await prisma.traceabilityBlockchain.update({
    where: { id: block.id },
    data: { is_valid: isValid },
  });

  return {
    found: true,
    is_valid: isValid,
    block_index: block.block_index,
    block_hash: block.block_hash,
    recomputed_hash: recomputedHash,
    detail: isValid
      ? "Data konsisten, tidak ada indikasi manipulasi."
      : "PERINGATAN: hash tidak cocok — data kemungkinan telah diubah di luar sistem.",
  };
};
