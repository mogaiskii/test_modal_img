from bottle import route, post, get, run, template, static_file, response, request
import os
import json
import requests
import urllib, http.client
import hmac, hashlib


nonce_file = "./nonce"
class YobitException(Exception):
    pass
        
def call_api(API_KEY,API_SECRET,**kwargs):

    # При каждом обращении к торговому API увеличиваем счетчик nonce на единицу
    with open(nonce_file, 'r+') as inp:
        nonce = int(inp.read())
        inp.seek(0)
        inp.write(str(nonce+1))
        inp.truncate()

    payload = {'nonce': nonce}

    if kwargs:
        payload.update(kwargs)
    payload =  urllib.parse.urlencode(payload)

    H = hmac.new(key=API_SECRET, digestmod=hashlib.sha512)
    H.update(payload.encode('utf-8'))
    sign = H.hexdigest()
    
    headers = {"Content-type": "application/x-www-form-urlencoded",
           "Key":API_KEY,
           "Sign":sign}
    conn = http.client.HTTPSConnection("yobit.net", timeout=60)
    conn.request("POST", "/tapi/", payload, headers)
    response = conn.getresponse().read()
    
    conn.close()

    try:
        obj = json.loads(response.decode('utf-8'))

        if 'error' in obj and obj['error']:
            raise YobitException(obj['error'])
        return obj
    except json.decoder.JSONDecodeError:
        raise YobitException('Ошибка анализа возвращаемых данных, получена строка', response)




@get('/check/<pair>')
def check(pair):
    response.headers['Content-Type'] = 'application/json'
    res = requests.get('https://yobit.net/api/3/ticker/'+pair)
    res_obj = json.loads(res.text)
    return json.dumps({str(pair): {"sell":res_obj[pair]['sell'],
                            "buy": res_obj[pair]['buy']}})

@post('/sell/<pair>')
def sell(pair):
    response.headers['Content-Type'] = 'application/json'
    API_KEY = request.POST.getunicode("api_key")
    API_SECRET = request.POST.getunicode("api_secret")
    API_SECRET = bytearray(API_SECRET, 'utf-8')
    if not os.path.exists(nonce_file):
        with open(nonce_file, "w") as out:
            out.write('1')

    rate = request.POST.getunicode("rate")
    amount = request.POST.getunicode("amount")
    return call_api(API_KEY,API_SECRET,method="Trade", pair=pair, type="sell", rate=rate, amount=amount)

@post('/buy/<pair>')
def buy(pair):
    response.headers['Content-Type'] = 'application/json'
    API_KEY = request.json()["api_key"]
    API_SECRET = request.json()["api_secret"]
    API_SECRET = bytearray(API_SECRET, 'utf-8')
    nonce_file = "./nonce"
    if not os.path.exists(nonce_file):
        with open(nonce_file, "w") as out:
            out.write('1')

    rate = request.json()["rate"]
    amout = request.json()["amount"]
    return call_api(API_KEY,API_SECRET,method="Trade", pair=pair, type="buy", rate=rate, amount=amount)




@route('/css/<filename>')
def index(filename):
    return static_file(filename, root="./css")
@route('/js/<filename>')
def index(filename):
    return static_file(filename, root="./js")
      
@route('/<filename>')
def index(filename):
    return static_file(filename, root="./")

run(host='localhost', port=8080, debug=True)