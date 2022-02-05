import _thread
import sys
import threading

import requests

Client_ID = None
sheet = None


def is_in(elements, content: iter):
    return any(element in content for element in elements)  # renvoie True si un element est dans content


def values_from_one(dictionary: dict, value):
    for values in list(dictionary.values()):
        if value in values:
            return values
    raise ValueError(f"Your dictionary not content {value}")


def multiple_replace(text: str, to_replace: iter, _in: iter) -> str:
    for pos, ch in enumerate(to_replace):
        if ch in text:
            text = text.replace(ch, _in[pos])
    return text


def generate_implicit(tuple_: tuple):
    for element in tuple_:
        yield element
        yield f"!{element}"


def set_client_id(client_id):
    global Client_ID
    Client_ID = client_id


def upload_image_on_imgur(*, url=None, file_path=""):
    # global Client_ID
    if Client_ID is None:
        raise ValueError("Client_ID doesn't set")
    if not file_path and not url or file_path and url:
        raise ValueError("Parameter are invalid")
    if url is not None:
        payload = {'image': requests.get(url).content}
    else:
        with open(file_path, "rb") as file:
            payload = {'image': file.read()}
    headers = {'Authorization': f'Client-ID {Client_ID}'}
    response = requests.post("https://api.imgur.com/3/image", headers=headers, data=payload)  # upload image
    return response.json()["data"]["link"]  # return the link of the image


def quit_function():
    sys.stderr.flush()  # Python 3 stderr is likely buffered.
    _thread.interrupt_main()  # raises KeyboardInterrupt


def exit_after(s):
    """
    Use as decorator to exit process if
    function takes longer than s seconds
    """
    def outer(fn):
        def inner(*args, **kwargs):
            timer = threading.Timer(s, quit_function)
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result
        return inner
    return outer
