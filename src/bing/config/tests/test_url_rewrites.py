import copy
from unittest.mock import patch

from django.test import TestCase

from zds_client import Client

from ..client import ClientWrapper
from ..models import URLRewrite


class RewriteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        URLRewrite.objects.create(
            from_value="https://zaken-api.vng.cloud",
            to_value="http://localhost:12018/vng/zrc",
        )
        URLRewrite.objects.create(
            from_value="https://documenten-api.vng.cloud",
            to_value="http://localhost:12018/vng/drc",
        )

        Client.load_config(dummy={"host": "localhost", "port": 443, "scheme": "https"})

        # client object is not relevant for this code path
        cls.wrapper = ClientWrapper(client=Client("dummy"))

    def setUp(self):
        super().setUp()

        patcher = patch.object(self.wrapper.client, "_log")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_noop(self):
        data = [
            {
                "foo": "bar",
                "nested": {"object": "with", "list": ["mixed", {"object": "types"}]},
                "not_string": 10,
            }
        ]

        original = copy.deepcopy(data)

        self.wrapper.rewrite_urls(data)

        self.assertEqual(data, original)

    def test_simple_dict(self):
        data = {"key": "https://documenten-api.vng.cloud/eio/123"}

        self.wrapper.rewrite_urls(data)

        self.assertEqual(data, {"key": "http://localhost:12018/vng/drc/eio/123"})

    def test_nested(self):
        data = {
            "key": "https://documenten-api.vng.cloud/eio/123",
            "list": [
                "https://documenten-api.vng.cloud/eio/123",
                "https://documenten-api.vng.cloud/eio/456",
            ],
            "list_of_objects": [{"otherkey": "https://zaken-api.vng.cloud/zaken/123"}],
        }

        self.wrapper.rewrite_urls(data)

        rewritten = {
            "key": "http://localhost:12018/vng/drc/eio/123",
            "list": [
                "http://localhost:12018/vng/drc/eio/123",
                "http://localhost:12018/vng/drc/eio/456",
            ],
            "list_of_objects": [
                {"otherkey": "http://localhost:12018/vng/zrc/zaken/123"}
            ],
        }
        self.assertEqual(data, rewritten)

    def test_request(self):
        request_data = {"key": "https://documenten-api.vng.cloud/eio/123"}
        response_data = {"url": "http://localhost:12018/vng/zrc/zaken/abc"}

        with patch.object(
            self.wrapper.client, "request", return_value=response_data
        ) as mock_request:
            response = self.wrapper.request(
                "https://example.com", "dummy_operation", json=request_data
            )

        mock_request.assert_called_once_with(
            "https://example.com",
            "dummy_operation",
            method="GET",
            json={"key": "http://localhost:12018/vng/drc/eio/123"},
        )

        self.assertEqual(response, {"url": "https://zaken-api.vng.cloud/zaken/abc"})

    def test_request_no_body(self):
        with patch.object(self.wrapper.client, "request") as mock_request:
            self.wrapper.request("https://example.com", "dummy_operation")

        mock_request.assert_called_once_with(
            "https://example.com", "dummy_operation", method="GET"
        )
