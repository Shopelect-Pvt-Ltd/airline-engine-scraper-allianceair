import requests
from html import unescape


def get_captcha_base64(data):
    """
    Get captcha result from base64 string
    """

    response = requests.post('http://2captcha.com/in.php', data={
        'key': "80a7f47ecec430e465df74b8c5fd69d4",
        'method': 'base64',
        'body': data,
        'json': 1,
        'regsense': 1
    }).json()

    captcha_id = response['request']

    # wait for captcha to be solved
    for i in range(1,4,1):
        response = requests.post('http://2captcha.com/res.php', data={
            'key': "80a7f47ecec430e465df74b8c5fd69d4",
            'action': 'get',
            'id': int(captcha_id)
        }).text
        if response == 'ERROR_CAPTCHA_UNSOLVABLE':
            print("captcha unsolvable error")
            return '000000'

        if '|' in response:
            _, captcha_text = unescape(response).split('|')
            return (captcha_id, captcha_text)


def mark_good(captcha_id):
    """
    Mark captcha as good
    """

    resp = requests.post('http://2captcha.com/res.php', data={
        'key': "9d29f472049e0abd5f0ec3a0e1a7df43",
        'action': 'reportgood',
        'id': int(captcha_id)
    })

    if resp.status_code == 200 and resp.text == 'OK_REPORT_RECORDED':
        print('Good captcha reported')
        return True
    else:
        print('Failed to report good captcha')
        return False


def mark_bad(captcha_id):
    """
    Mark captcha as bad
    """

    resp = requests.post('http://2captcha.com/res.php', data={
        'key': "9d29f472049e0abd5f0ec3a0e1a7df43",
        'action': 'reportbad',
        'id': int(captcha_id)
    })

    if resp.status_code == 200 and resp.text == 'OK_REPORT_RECORDED':
        print('Bad captcha reported')
        return True
    else:
        print('Failed to report bad captcha')
        return False