import sys
# print("Python executable:", sys.executable)
# print("Python path:", sys.path)

from diffusers import StableDiffusionPipeline
# print("diffusers is installed and can be imported")

from auth_token import auth_token
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import torch
from torch import autocast
from io import BytesIO
import base64 
# from diffusers import StableDiffusionPipeline
import os
os.environ['HF_HUB_DISABLE_SSL_VERIFY'] = '1'

app = FastAPI()

app.add_middleware(
    CORSMiddleware, 
    allow_credentials=True, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

### check if cuda is available
if not torch.cuda.is_available():
    device = "cpu"
else:
    device = "cuda"

model_id = "CompVis/stable-diffusion-v1-4"
pipe = StableDiffusionPipeline.from_pretrained(model_id, revision="fp16", torch_dtype=torch.float16, use_auth_token=auth_token)
pipe.to(device)

@app.get("/")
def generate(prompt: str): 
    with autocast(device): 
        image = pipe(prompt, guidance_scale=8.5).images[0]

    image.save("testimage.png")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    imgstr = base64.b64encode(buffer.getvalue())

    return Response(content=imgstr, media_type="image/png")


