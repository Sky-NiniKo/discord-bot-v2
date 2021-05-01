import requests

Client_ID = None
sheet = None


def is_in(elements, content: iter):
    return any(element in content for element in elements)  # renvoir True si un element est dans content


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
    global Client_ID
    if Client_ID is None:
        raise ValueError("Client_ID doesn't set")
    if not file_path and not url or file_path and url:
        raise ValueError("Parameter are invalid")
    if url is not None:
        payload = {'image': requests.get(url).content}
    else:
        with open(file_path, "rb") as file:
            payload = {'image': file.read()}
    api = "https://api.imgur.com/3/image"
    headers = {'Authorization': f'Client-ID {Client_ID}'}
    response = requests.request("POST", api, headers=headers, data=payload, files=[])  # upload image
    rep = str(response.text.encode('utf-8')[2:-1])  # convert response in string
    return "https://i.imgur.com/" + rep[rep.find("link") + 33:rep.find(".png") + 4]  # return the link of the image