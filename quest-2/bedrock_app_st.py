import io
import json

import boto3
import streamlit as st
from PIL import Image

st.title("Building with Bedrock")  # Title of the application
st.subheader("Model Playground")

# Turn base64 string to image with PIL
def base64_to_pil(base64_string):
    """
    Purpose:
        Turn base64 string to image with PIL
    Args/Requests:
         base64_string: base64 string of image
    Return:
        image: PIL image
    """
    import base64

    imgdata = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(imgdata))
    return image


bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-west-2",
)


# Bedrock api call to stable diffusion
def generate_image_sd(text):
    """
    Purpose:
        Uses Bedrock API to generate an Image
    Args/Requests:
         text: Prompt
    Return:
        image: base64 string of image
    """
    body = {
        "prompt": text,
        "output_format": "jpeg",
        "seed": 0,
    }

    body = json.dumps(body)

    modelId = "stability.stable-image-core-v1:1"

    response = bedrock_runtime.invoke_model(
        body=body, 
        modelId=modelId
    )
    response_body = json.loads(response["body"].read().decode("utf-8"))

    results = response_body["images"][0]
    return results

def call_nova_lite(
    system_prompt: str,
    prompt: str,
    model_id: str = "us.amazon.nova-lite-v1:0",
):
    prompt_config = {
        "system": [
            {"text": system_prompt}
        ],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"text": prompt},
                ],
            }
        ],
    }
    body = json.dumps(prompt_config)

    modelId = model_id
    accept = "application/json"
    contentType = "application/json"

    response = bedrock_runtime.invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=contentType
    )
    response_body = json.loads(response.get("body").read())

    results = response_body["output"]["message"]["content"][0].get("text")
    return results

models = ["Stable Image Core", "Amazon Nova Lite"]

current_model = st.selectbox("Select Model", models)


if current_model == "Stable Image Core":
    # text input
    prompt = st.text_area("Enter prompt")

    #  Generate image from prompt,
    if st.button("Generate Image"):
        # # TODO generate image

        # image = None
        # st.image(image)

if current_model == "Amazon Nova Lite":
    # TODO System Prompt input

    # TODO Prompt input

    #  Generate text from prompt,
    if st.button("Call Nova"):
        # TODO generate text

        generated_text = "REPLACE WITH Generated text"
        st.markdown(generated_text)
