# Copyright 2024 MaiCall
# @author: Ihor Pysmennyi (<support@maicall.ai>)
# License LGPL-3 (https://www.odoo.com/documentation/17.0/legal/licenses.html).
import json
import base64
from typing import Dict, List, Union, Any
from odoo import http
from odoo.http import request, content_disposition

headers = {'Content-Type': 'application/json'}


class CallCenterController(http.Controller):

    @staticmethod
    def response_ok(message: Union[str, List[Dict], Dict['str', Any]] = None):
        return request.make_response(json.dumps({
            'status': 'ok',
            'message': message,
        }), headers=headers, status=200)

    @staticmethod
    def response_error(message: str, status: int):
        return request.make_response(json.dumps({
            'status': 'error',
            'message': message,
        }), headers=headers, status=status)

    @http.route('/public/download/<string:token>', type='http', auth='public', website=True)
    def download_file(self, token, **kwargs):
        file_record = request.env['evo.call'].sudo().search(
            [('download_token', '=', token)], limit=1)
        if not file_record or not file_record.audio_file:
            return request.not_found()
        file_content = base64.b64decode(file_record.audio_file)
        file_name = file_record.audio_file_name or "downloaded_file"

        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', content_disposition(file_name))
            ]
        )
