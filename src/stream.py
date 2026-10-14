# Implement Azure OpenAI async chat client for streaming responses

import asyncio
import os
from typing import AsyncGenerator
from openai import AsyncAzureOpenAI


# Create an asynchronous AzureOpenChatClient to interact with the Azure OpenAI API.
# The chat client requires an API endpoint, deployment name, key, and version function
class AzureOpenAIChatClient:

    def __init__(self):
        self.aclient = AsyncAzureOpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            api_version=os.environ["OPENAI_API_VERSION"],
            azure_endpoint=os.environ["OPENAI_API_ENDPOINT"],
            azure_deployment=os.environ["OPENAI_API_DEPLOYMENT"],
        )

    # Define chat stream asynchrnous generator method that yields each output token from the API
    async def chat_stream(
            self,
            prompt: str,
            model: str = "gpt-4o-mini"
    ) -> AsyncGenerator:

        stream = await self.aclient.chat.completions.create(

            messages=[
                {
                    "role": "user",
                    "content":prompt
                }
            ],
            model=model,

            # set the stream=True to recieve output from the API instead of the full response at once
            stream=True 
        )


        # Loop over stream and yeild each output token or return empty string if delta.content is empty
        async for chunk in stream:
            # the data: is prefix to each token so that browsers can correctly parse the content using the EventSource API 
            yield f"data: {chunk.choices[0].delta.content or ''}\n\n"

            # Slow down the streaming rate to reduce back pressure on the clients
            await asyncio.sleep(0.05)


        yield f"data: [DONE]\n\n"



if __name__=="__main__":

    # I create an instance of AsyncAzureOpenAI, which allows us to chat with Azure OpenAI models via an API in our private Azure environment
    azure_chat_client = AzureOpenAIChatClient()

    """
    Note:
        - By setting stream=True -> AsyncAzureOpenAI returns a data stream(an async generator function) instead of the full model response
        - I can loop over the data stream and yeild tokens with data: prefix to comply with the SSE specification
        This will let browser automatically parse the stream content using the 'EventSource' web API

        V.I
        * When exposing streaming endpoints, I should know how fast the clients can consume the data
        I am sending them.

        A good practice is to reduce the streaming rate ~ asyncio.sleep(0.05) to reduce the back pressure on clients
    
    """



# SSE with GET Request
# I can implement the SSE with endpoint by passing the chat stream to the FastAPI 'StreamingResponse' as a GET endpoint

# Implementing an SSE endpoint using FastAPI StreamingResponse
from fastapi.responses import StreamingResponse
#from stream import azure_chat_client
from fastapi import FastAPI

app = FastAPI()


# Implement an SSE endpoint with the GET method to use with the EventSource API om the browser
@app.get("/generate/text/stream")
async def serve_text_to_text_stream_controller(
    prompt: str,
) -> StreamingResponse:

    # Pass the chat_stream generator to the StreamResponse to forward output as it is being generated to the client
    # Set the media_type = text/event-stream as per SSE specifications so that browsers can handle the response correctlt
    return StreamingResponse(
        azure_chat_client.chat_stream(prompt), media_type="text/event-stream"
    )

# Implementing SSE on the client using the browser EventSource API

"""
pages/client-sse.html

Create a simple HTML input and button for intiating SSE requests
<input type="text" id="messageInput" placeholder="Enter your prompt">

Create an empty container to be used as a sink for the stream content
<div style="padding-top: 10px" id="responseContainer"></div> 


Listen for button clicks and run the SSE callback
button.addEventListener('click', function() { 
        const message = input.value;
        const url = 'http://localhost:8000/generate/text/stream?prompt=' +
            encodeURIComponent(message);


        resetForm() 

Create a new EventSoruce ibject to listen conntection state to handle events
source = new EventSource(url);


Log to console when an SSE connection is opened. Handle each message by rendering message content
to the response container until the [DONE] message is received, which signals that the connection 
should now be closed. Additionally, close the connection if any errors occur and log the error to the browser’s console.

source.addEventListener('open', handleOpen, false);
source.addEventListener('message', handleMessage, false);
source.addEventListener('error', handleClose, false);


With the SSE client implemented, I can use it to test our SSE endpoint, but I need to serve the HTML first.

1) Create a page directory and then place the HTML file inside.
2) Then mount the directory onto our FastAPI server to serve it content as static file
3) Via mounting, FastAPI takes care of mapping API paths to each file so that you can access them with a browser from the same origin as your server.


By implementing the code below, I serve the HTML from the same origin as our API server.
This avoids triggering the browser CORS security machanism, which can block outgoing requests 
reaching our server.

I can now access the HTML page by visiting
http://localhost:8000/pages/sse-client.html



Apply CORS

Congratulations! You now have a full working solution where model responses are directly streamed to your client as soon as generated data 
becomes available.

Better user experience with the chatbot as they recieve responses in real-time



Our solution implemented concurrency using an asynchronous client for interacting with the Azure OpenAI API API to stream faster response.



"""



# Mounting HTML files on the servers as static assets
from fastapi.staticfiles import StaticFiles
# Mount the pages directory onto the /pages to serve its content as static assets
# Once mounted, you can access each file by visiting <origin>/pages/<filename>
app.mount("/pages", StaticFiles(directory="pages"), name="pages")