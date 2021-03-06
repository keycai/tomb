#!/usr/bin/env python
#coding:utf-8
#Copyright (C) dirlt

from flask import Flask
from flask import make_response
from flask import request

app = Flask(__name__)
app.debug = True

from common2 import *
p = Process()
from ofpay import OFPayer
ofp = OFPayer()

import traceback
import json

def retry(func, args, cond, count = 3):
    res = None
    while count > 0:
        try:
            (ok, retval) = apply(func, args)
        except Exception as e:
            # 发生异常
            app.logger.warning(traceback.format_exc())
            count -= 1
            continue
        res = (ok, retval)
        if not cond(ok, retval): # 不满足条件
            count -= 1
            continue
        else: break
    return res

def make_resp(js, cb):
    if type(js) == 'str': s = js
    else: s = json.dumps(js)
    if cb:
        s = cb + '(%s)' % s
        resp = make_response(s)
        resp.headers['Content-Type'] = 'application/javascript'
    else:
        resp = make_response(s)
        resp.headers['Content-Type'] = 'text/json'
    return resp

@app.route('/init', methods = ['GET'])
def init():
    phone = request.args.get('phone')
    cb = request.args.get('cb', '')
    assert(phone)
    res = retry(p.above_half, (phone,), lambda ok, res: True)
    if not res:
        # 查询验证码失败
        js = {'code': 1, 'msg':'get captcha faild'}
    else:
        (ok, res) = res
        # 已经查询到余额
        if ok: js = {'code':0, 'msg':'bal', 'data': res}
        # 否则返回token
        else: js = {'code':0, 'msg':'token', 'data': res}
    return make_resp(js, cb)

@app.route('/query', methods = ['GET'])
def query():
    token = request.args.get('token')
    code = request.args.get('code')
    cb = request.args.get('cb', '')
    assert(token and code)
    res = retry(p.bottom_half, (token, code), lambda ok, res: ok)
    if not res or not res[0]:
        # 查询余额失败
        msg = 'query balance failed'
        if res: msg += ': %s' % res[1]
        js = {'code': 1, 'msg': msg}
    else:
        js = {'code': 0, 'msg': 'bal', 'data': res[1]}
    return make_resp(js, cb)

# todo(dirlt): 安全性如何保证, 用POST + HTTPS ?
@app.route('/charge', methods = ['GET'])
def charge():
    phone = request.args.get('phone')
    cardnum = int(request.args.get('cardnum', '2'))
    uid = request.args.get('uid')
    cb = request.args.get('cb', '')
    assert(phone and uid)
    # uid = ofp.gen_uid()
    ts = ofp.current_time()
    ofp.pre_charge(uid, ts, cardnum, phone)
    kv = ofp.do_charge()
    (code, msg) = ofp.post_charge(kv)
    js = {'code': code, 'msg': msg}
    return make_resp(js, cb)

@app.route('/charge-cb', methods = ['POST'])
def charge_cb():
    retcode = int(request.form['ret_code'])
    spid = request.form['sporder_id']
    ofp.update_charge_status(spid, retcode)
    return make_resp('OK', '')

@app.route('/history', methods = ['GET'])
def history():
    phone = request.args.get('phone')
    period = int(request.args.get('period', '30'))
    limit = int(request.args.get('limit', '10'))
    cb = request.args.get('cb', '')
    assert(phone)
    limit = min(limit, 30)
    s = ofp.query_charge_history(phone, period, limit)
    return make_resp(s, cb)

if __name__ == '__main__':
    app.run()
