import { pool } from "../db/mysql";
import { GENESIS_HASH, buildBlockData, computeHash } from "./blockchain_hash";

export const syncBlock = async (batch: any) => {
  const [kebunRows]: any = await pool.query("SELECT * FROM kebun WHERE id = ?", [batch.kebun_id]);
  const kebun = kebunRows[0];
  if (!kebun) throw new Error("Kebun not found");

  const [petaniRows]: any = await pool.query("SELECT * FROM users WHERE id = ?", [kebun.petani_id]);
  const petani = petaniRows[0];
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

  const [existingBlockRows]: any = await pool.query(
    "SELECT * FROM traceability_blockchain WHERE batch_id = ?",
    [batch.id]
  );
  const existingBlock = existingBlockRows[0];

  if (existingBlock) {
    const newHash = computeHash(blockDataObj, existingBlock.previous_hash);
    await pool.query(
      "UPDATE traceability_blockchain SET block_data = ?, block_hash = ?, is_valid = 1, updated_at = NOW() WHERE id = ?",
      [blockDataString, newHash, existingBlock.id]
    );
    const [updatedBlockRows]: any = await pool.query("SELECT * FROM traceability_blockchain WHERE id = ?", [existingBlock.id]);
    return updatedBlockRows[0];
  }

  const [lastBlockRows]: any = await pool.query("SELECT * FROM traceability_blockchain ORDER BY block_index DESC LIMIT 1");
  const lastBlock = lastBlockRows[0];

  const blockIndex = lastBlock ? lastBlock.block_index + 1 : 0;
  const previousHash = lastBlock ? lastBlock.block_hash : GENESIS_HASH;
  const blockHash = computeHash(blockDataObj, previousHash);

  const [result]: any = await pool.query(
    "INSERT INTO traceability_blockchain (batch_id, block_data, block_hash, previous_hash, block_index, is_valid, validated_at, updated_at) VALUES (?, ?, ?, ?, ?, 1, NOW(), NOW())",
    [batch.id, blockDataString, blockHash, previousHash, blockIndex]
  );

  const [newBlockRows]: any = await pool.query("SELECT * FROM traceability_blockchain WHERE id = ?", [result.insertId]);
  return newBlockRows[0];
};

export const verifyBlock = async (batchId: number) => {
  const [blockRows]: any = await pool.query("SELECT * FROM traceability_blockchain WHERE batch_id = ?", [batchId]);
  const block = blockRows[0];

  if (!block) {
    return { found: false, is_valid: null, detail: "Block tidak ditemukan untuk batch ini." };
  }

  const blockDataObj = JSON.parse(block.block_data);
  const recomputedHash = computeHash(blockDataObj, block.previous_hash);
  const isValid = recomputedHash === block.block_hash;

  await pool.query(
    "UPDATE traceability_blockchain SET is_valid = ? WHERE id = ?",
    [isValid ? 1 : 0, block.id]
  );

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
