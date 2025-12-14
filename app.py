import gradio as gr
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from PyPDF2 import PdfReader
import textwrap

# --- 1. SETUP MODEL (CPU Safe) ---
# We use flan-t5-large as verified in Colab
checkpoint = "google/flan-t5-large"
print(f"Loading {checkpoint}...")

tokenizer = AutoTokenizer.from_pretrained(checkpoint)

# CRITICAL CHANGE: Use float32 for CPU stability
model = AutoModelForSeq2SeqLM.from_pretrained(
    checkpoint,
    device_map="auto",
    torch_dtype=torch.float32 
)

# --- 2. LOGIC FUNCTIONS ---
def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        return full_text
    except Exception as e:
        return f"Error reading PDF: {e}"

def simplify_text(text):
    # SAME LOGIC: 1500 chars per chunk
    chunks = textwrap.wrap(text, 1500)
    simplified_output = []
    
    print(f"Processing {len(chunks)} chunks...")

    for chunk in chunks:
        # SAME LOGIC: Your specific prompt
        prompt = "Summarize the key points of this text in clear, simple English: " + chunk
        
        # CRITICAL CHANGE: Remove .to("cuda"). 
        # We just tokenize normally. The model is already on the correct device (CPU).
        input_ids = tokenizer(prompt, return_tensors="pt").input_ids
        
        # SAME LOGIC: Your specific parameters (repetition_penalty=2.0, etc.)
        outputs = model.generate(
            input_ids,
            max_new_tokens=200,
            min_length=50,
            repetition_penalty=2.0,
            no_repeat_ngram_size=3
        )
        
        decoded_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
        simplified_output.append(decoded_output)
    
    return "\n\n".join(simplified_output)

# --- 3. BRIDGE & UI ---
def process_pipeline(pdf_file):
    if pdf_file is None:
        return "Please upload a PDF file first!"
    
    # Extract
    raw_text = extract_text_from_pdf(pdf_file.name)
    if raw_text.startswith("Error"):
        return raw_text

    # Simplify
    return simplify_text(raw_text)

# SAME UI LAYOUT
demo = gr.Interface(
    fn=process_pipeline,
    inputs=gr.File(label="Upload Research Paper (PDF)"),
    outputs=gr.Textbox(label="Simplified Version", lines=15),
    title="The Jargon Buster - Research Paper Simplifier 🤖",
    description="Upload a complex PDF. This AI will summarize key points in simple English."
)

# CRITICAL CHANGE: No 'share=True' needed for Spaces
demo.launch()
