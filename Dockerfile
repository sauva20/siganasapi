# Gunakan image Python resmi
FROM python:3.10

# Set working directory
WORKDIR /code

# Salin requirements dan install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Set up user untuk Hugging Face Spaces (Wajib non-root)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Pindah ke home direktori user
WORKDIR $HOME/app

# Salin semua file project ke dalam container dengan ownership user
COPY --chown=user . $HOME/app

# Buat folder untuk simpan model jika belum ada
RUN mkdir -p weights && chown -R user:user weights

# Jalankan server FastAPI di port 7860 (Port wajib Hugging Face Spaces)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
