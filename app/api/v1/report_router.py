from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.batch import BatchPanen
from app.models.kebun import Kebun
from app.models.user import RoleEnum, User

router = APIRouter(prefix="/reports", tags=["Laporan Dinas Pertanian"])


@router.get("/summary")
def summary_overview(
    tanggal_mulai: Optional[date] = Query(None, description="Filter tanggal panen mulai"),
    tanggal_selesai: Optional[date] = Query(None, description="Filter tanggal panen selesai"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.dinas_pertanian)),
):
    """
    Ringkasan agregat seluruh batch: total nanas per grade, total kebun aktif,
    total petani terlibat. Untuk kartu ringkasan di halaman utama dashboard.
    """
    query = db.query(BatchPanen)
    if tanggal_mulai:
        query = query.filter(BatchPanen.tanggal_panen >= tanggal_mulai)
    if tanggal_selesai:
        query = query.filter(BatchPanen.tanggal_panen <= tanggal_selesai)

    agg = query.with_entities(
        func.count(BatchPanen.id).label("total_batch"),
        func.coalesce(func.sum(BatchPanen.total_buah), 0).label("total_buah"),
        func.coalesce(func.sum(BatchPanen.jumlah_grade_a), 0).label("total_grade_a"),
        func.coalesce(func.sum(BatchPanen.jumlah_grade_b), 0).label("total_grade_b"),
        func.coalesce(func.sum(BatchPanen.jumlah_grade_c), 0).label("total_grade_c"),
        func.coalesce(func.sum(BatchPanen.jumlah_reject), 0).label("total_reject"),
        func.coalesce(func.sum(BatchPanen.total_berat_kg), 0).label("total_berat_kg"),
    ).first()

    total_kebun_aktif = db.query(func.count(Kebun.id)).filter(Kebun.is_active == True).scalar()
    total_petani = db.query(func.count(func.distinct(Kebun.petani_id))).filter(
        Kebun.is_active == True
    ).scalar()

    total_buah = agg.total_buah or 0
    reject_pct = round((agg.total_reject / total_buah * 100), 2) if total_buah else 0.0

    return {
        "periode": {"mulai": tanggal_mulai, "selesai": tanggal_selesai},
        "total_batch": agg.total_batch,
        "total_buah": total_buah,
        "total_berat_kg": float(agg.total_berat_kg),
        "komposisi_grade": {
            "grade_a_ekspor": agg.total_grade_a,
            "grade_b_premium_lokal": agg.total_grade_b,
            "grade_c_standar": agg.total_grade_c,
            "reject": agg.total_reject,
        },
        "persentase_food_loss": reject_pct,  # indikator target SDG 2 di proposal
        "total_kebun_aktif": total_kebun_aktif,
        "total_petani_terlibat": total_petani,
    }


@router.get("/per-lokasi")
def summary_per_lokasi(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.dinas_pertanian)),
):
    """
    Rekap produksi & komposisi grade dikelompokkan per kecamatan
    (Jalancagak, Cijambe, Cirangkong, dst) — untuk monitoring pemerataan
    kualitas antar lokasi validasi.
    """
    rows = (
        db.query(
            Kebun.kecamatan,
            func.count(func.distinct(Kebun.id)).label("jumlah_kebun"),
            func.count(func.distinct(Kebun.petani_id)).label("jumlah_petani"),
            func.coalesce(func.sum(BatchPanen.total_buah), 0).label("total_buah"),
            func.coalesce(func.sum(BatchPanen.jumlah_grade_a), 0).label("grade_a"),
            func.coalesce(func.sum(BatchPanen.jumlah_grade_b), 0).label("grade_b"),
            func.coalesce(func.sum(BatchPanen.jumlah_grade_c), 0).label("grade_c"),
            func.coalesce(func.sum(BatchPanen.jumlah_reject), 0).label("reject"),
        )
        .outerjoin(BatchPanen, BatchPanen.kebun_id == Kebun.id)
        .filter(Kebun.is_active == True)
        .group_by(Kebun.kecamatan)
        .all()
    )

    return [
        {
            "kecamatan": r.kecamatan or "Tidak diisi",
            "jumlah_kebun": r.jumlah_kebun,
            "jumlah_petani": r.jumlah_petani,
            "total_buah": r.total_buah,
            "komposisi_grade": {
                "grade_a_ekspor": r.grade_a,
                "grade_b_premium_lokal": r.grade_b,
                "grade_c_standar": r.grade_c,
                "reject": r.reject,
            },
        }
        for r in rows
    ]


@router.get("/per-petani")
def summary_per_petani(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.dinas_pertanian)),
):
    """
    Rekap performa grading per petani — dipakai Dinas Pertanian untuk
    pembinaan (petani mana yang butuh pendampingan lebih, dsb).
    """
    rows = (
        db.query(
            User.id.label("petani_id"),
            User.nama_lengkap,
            func.count(func.distinct(Kebun.id)).label("jumlah_kebun"),
            func.count(func.distinct(BatchPanen.id)).label("jumlah_batch"),
            func.coalesce(func.sum(BatchPanen.total_buah), 0).label("total_buah"),
            func.coalesce(func.sum(BatchPanen.jumlah_grade_a), 0).label("grade_a"),
            func.coalesce(func.sum(BatchPanen.jumlah_grade_b), 0).label("grade_b"),
            func.coalesce(func.sum(BatchPanen.jumlah_grade_c), 0).label("grade_c"),
            func.coalesce(func.sum(BatchPanen.jumlah_reject), 0).label("reject"),
        )
        .join(Kebun, Kebun.petani_id == User.id)
        .outerjoin(BatchPanen, BatchPanen.kebun_id == Kebun.id)
        .filter(User.role == RoleEnum.petani, Kebun.is_active == True)
        .group_by(User.id, User.nama_lengkap)
        .all()
    )

    return [
        {
            "petani_id": r.petani_id,
            "nama_petani": r.nama_lengkap,
            "jumlah_kebun": r.jumlah_kebun,
            "jumlah_batch": r.jumlah_batch,
            "total_buah": r.total_buah,
            "komposisi_grade": {
                "grade_a_ekspor": r.grade_a,
                "grade_b_premium_lokal": r.grade_b,
                "grade_c_standar": r.grade_c,
                "reject": r.reject,
            },
        }
        for r in rows
    ]
