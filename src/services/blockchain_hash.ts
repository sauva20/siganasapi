import crypto from "crypto";

export const GENESIS_HASH = "0".repeat(64);

const serialize = (data: any): string => {
  // Sort keys deeply to ensure deterministic output
  const sortObject = (obj: any): any => {
    if (obj === null || typeof obj !== "object") return obj;
    if (Array.isArray(obj)) return obj.map(sortObject);
    return Object.keys(obj)
      .sort()
      .reduce((result: any, key: string) => {
        result[key] = sortObject(obj[key]);
        return result;
      }, {});
  };
  return JSON.stringify(sortObject(data));
};

export const computeHash = (blockData: any, previousHash: string): string => {
  const content = serialize({
    block_data: blockData,
    previous_hash: previousHash,
  });
  return crypto.createHash("sha256").update(content, "utf8").digest("hex");
};

export const buildBlockData = (
  batch_id: number,
  kode_batch: string,
  kebun_id: number,
  petani_id: number,
  nama_petani: string,
  nama_kebun: string,
  latitude: number,
  longitude: number,
  tanggal_panen: string | Date,
  varietas_nanas: string,
  jenis_pupuk: string | null,
  total_buah: number,
  jumlah_grade_a: number,
  jumlah_grade_b: number,
  jumlah_grade_c: number,
  jumlah_reject: number,
  total_berat_kg: number
) => {
  return {
    batch_id,
    kode_batch,
    petani: {
      id: petani_id,
      nama: nama_petani,
    },
    kebun: {
      id: kebun_id,
      nama: nama_kebun,
      latitude,
      longitude,
      varietas: varietas_nanas,
      jenis_pupuk,
    },
    panen: {
      tanggal: typeof tanggal_panen === 'string' ? tanggal_panen : tanggal_panen.toISOString().split('T')[0],
      total_buah,
      total_berat_kg,
    },
    grading_summary: {
      grade_a: jumlah_grade_a,
      grade_b: jumlah_grade_b,
      grade_c: jumlah_grade_c,
      reject: jumlah_reject,
    },
    timestamp_created: new Date().toISOString(),
  };
};

export const verifyBlock = (blockData: any, storedHash: string, previousHash: string): boolean => {
  const expectedHash = computeHash(blockData, previousHash);
  return expectedHash === storedHash;
};
