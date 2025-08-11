# Copyright 2025 MaiCall
# @author: Serhii Mishchenko (<support@maicall.ai>)
# License LGPL-3 (https://www.odoo.com/documentation/17.0/legal/licenses.html).
import logging
from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BaseModelExtension(models.AbstractModel):
    _inherit = 'base'

    def prepare_field_char_value(self, field_char: str, record=None, tz=None):
        value = self.get_field_char_value(field_char, record)
        if value is None:
            return None
        field_type = self.get_field_char_type(field_char, record)
        if field_type == 'datetime' and tz:
            value = value.astimezone(tz)
            value = value.replace(tzinfo=None)
            value = value.strftime("%Y-%m-%d %H:%M:%S")
        return value

    def get_field_char_value(self, field_char: str, record=None):
        if not field_char or not record:
            return None
        try:
            result = record
            for attr in field_char.split('.'):
                result = getattr(result, attr, None)
                if result is None:
                    return None
            return result
        except Exception as e:
            _logger.error(f"Error preparing field char value: {e}")
            return None

    # pylint: disable=inconsistent-return-statements
    def get_field_char_type(self, field_char: str, record=None):
        if not field_char or not record:
            return None
        try:
            model = record.__class__
            field_parts = field_char.split('.')

            for i, part in enumerate(field_parts):
                field = model._fields.get(part)
                if not field:
                    return None

                if i < len(field_parts) - 1:
                    if hasattr(field, 'comodel_name'):
                        model = record.env[field.comodel_name]
                        record = getattr(record, part, None)
                        if record is None:
                            return None
                    else:
                        return None
                else:
                    return field.type
        except Exception as e:
            _logger.error(f"Error getting field char type: {e}")
            raise UserError(
                f"Error getting field char type: {e}"
            )
