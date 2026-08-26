import gradio as gr
from app.main import app as custom_api

# Membuat tampilan UI sederhana dari Gradio agar Hugging Face mengizinkan ini berjalan di versi Gratis
demo = gr.Interface(
    fn=lambda: "Siganas API is Running Successfully!", 
    inputs=None, 
    outputs="text",
    title="Siganas API",
    description="Backend FastAPI Server untuk Sistem Grading Nanas."
)

# Menggabungkan FastAPI kita dengan Gradio
app = gr.mount_gradio_app(custom_api, demo, path="/")
