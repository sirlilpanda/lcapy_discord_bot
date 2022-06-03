from discord.ext import commands
from discord.ext.commands.context import Context
from discord.channel import TextChannel
from discord import File, Attachment
from typing import Optional, Union
from lcapy import Circuit
from pdf2image import convert_from_path
import requests, os, asyncio
#alot of this imports are just for type hinting

TOKEN = "do what the last one said"
BOT = commands.Bot(command_prefix="!")

REQUEST_QUEUE = []

class RequestMessage:
    """creates a request message data type"""
    def __init__(self, ctx : Context, args : str) -> None:
        self.name : str = str(abs(hash(str(ctx.author) + str(ctx.message))))
        #this is the funky way i worked out how to have items in the queue that 
        #do not share the same name
        self.ctx : Context = ctx
        self.args : str = args

@BOT.event
async def on_ready() -> None: print("bot is working")


async def send_message() -> None:    
    """constant loop to check if there is a
       job waiting for it"""
    char_list = ["|", "/", "-", "\\"]
    i = 0

    while True: #before you ask yes i did try it while len(REQUEST_QUEUE) >= 1 and it did not work
        global REQUEST_QUEUE
        print(char_list[i%4], f"waiting for queue, items : {len(REQUEST_QUEUE)}", end="\r")
        if len(REQUEST_QUEUE) >= 1:
            channel, mess, worked = complete_request(REQUEST_QUEUE.pop())
            if worked:
                with open(mess.name+".jpg", "rb") as fh:
                    #pretty sure this slows it down but it doesnt need to be that fast
                    await channel.send(
                        f"{mess.ctx.author.mention} Circuit:",
                        file = File(fh, filename=mess.name+".jpg",)
                        )
                os.remove(mess.name+".jpg")
            else:
                await channel.send(f"Circuit FAILED\nreason :\n{mess}")
        else:
            await asyncio.sleep(1)
        i += 1



def complete_request(request : RequestMessage) -> tuple[TextChannel, Union[RequestMessage, str], bool]:
    """this completes the request given by the REQUEST_QUEUE
       of a error occours at anystep it should return the error
       and post it to discord"""
    e = gen_circuit(
        open_file(request.ctx.message.attachments[0], request.name) if "-file" in request.args else request.args.strip('`'),
        request.name)
    if e:
        return request.ctx.channel, e, False
    else:
        q = convert_to_image(request.name)
        if q:
            return request.ctx.channel, q, False

    return request.ctx.channel, request, True


@BOT.command()
async def circuit(ctx : Context, *, arg) -> None:
    """Adds the current job to queue to be ran"""
    REQUEST_QUEUE.append(RequestMessage(ctx, arg))
    print(f"REQUEST MADE\n\tREQUEST NAME : {str(abs(hash(str(ctx.author) + str(ctx.message))))}")
    await ctx.send(f"request now in queue {ctx.author} \nqueue postion {len(REQUEST_QUEUE)}")

def open_file(url : Attachment, name : str) -> str:
    """downloads, writes and reads the attach file on the message"""
    return (requests.get(url, allow_redirects=True).content).decode('utf-8')
    
def gen_circuit(string : str, name: str) -> Optional[str]:
    """generates the ciruit as a pdf with name for
    conversion if the generation fails then it will 
    return the error message"""
    try:
        cct = Circuit(string)
        cct.draw(filename=name+".pdf")
    except Exception as e:
        print(e)
        return e

def convert_to_image(name: str) -> Optional[str]:
    """converts the pdf given by the gen_circuit
    to an image for being posted"""
    pdf = convert_from_path(name+".pdf")
    if len(pdf) > 1:
        os.remove(name+".pdf")
        return "please use a smaller circuit"
    else:
        os.remove(name+".pdf")
        pdf[0].save(name+".jpg", 'JPEG')



BOT.loop.create_task(send_message())
BOT.run(TOKEN)