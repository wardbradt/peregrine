import logging
__all__ = [
    'FormatForLogAdapter',
    'format_for_log',
]


def format_for_log(msg, **kwargs):
    result = ''
    for key, value in kwargs.items():
        key = str(key).upper()
        # if key is not Labels or if the value for labels is not a list
        if key != 'LABELS':
            result += '{}#{} - '.format(key, value)
        else:
            for label in value:
                result += '{}#{} - '.format('label', label)

    result += msg
    return result


class FormatForLogAdapter(logging.LoggerAdapter):

    def __init__(self, logger, extra=None):
        super().__init__(logger, extra or {})

    def log(self, level, msg, *args, exc_info=None, extra=None, stack_info=False, **kwargs):
        if self.isEnabledFor(level):
            self.logger._log(level, format_for_log(msg, **kwargs), (), exc_info=exc_info, extra=extra,
                             stack_info=stack_info)
