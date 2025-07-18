from handlers.test import handler as test_handler


def test_lambda_handler(event, context):
    return test_handler(event, context)
