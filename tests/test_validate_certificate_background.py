import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.application.validate_certificate_background import ValidateCertificateBackground
from src.domain.exception.invalid_certificate_background import InvalidCertificateBackground


def _image_bytes(size, image_format="PNG") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, (255, 255, 255)).save(buffer, format=image_format)
    return buffer.getvalue()


def _response(url: str, content: bytes, status_code: int = 200) -> httpx.Response:
    return httpx.Response(status_code, content=content, request=httpx.Request("GET", url))


class ValidateCertificateBackgroundTestCase(unittest.TestCase):
    URL = "https://tech.floripa.br/wp-content/uploads/fundo.png"

    def setUp(self):
        self.validator = ValidateCertificateBackground()
        patcher = patch("src.application.validate_certificate_background.httpx.Client")
        self.client_class = patcher.start()
        self.addCleanup(patcher.stop)
        self.client = MagicMock()
        self.client_class.return_value.__enter__.return_value = self.client

    def _serve(self, content: bytes, status_code: int = 200):
        self.client.get.side_effect = lambda url: _response(url, content, status_code)

    def test_accepts_png_with_standard_size(self):
        self._serve(_image_bytes((1200, 627)))
        self.validator.execute([self.URL])

    def test_accepts_jpeg_with_standard_size(self):
        self._serve(_image_bytes((1200, 627), "JPEG"))
        self.validator.execute([self.URL])

    def test_rejects_off_standard_size_with_actual_dimensions(self):
        self._serve(_image_bytes((2000, 1414)))
        with self.assertRaises(InvalidCertificateBackground) as ctx:
            self.validator.execute([self.URL])
        self.assertIn("2000×1414", ctx.exception.message)
        self.assertIn("1200×627", ctx.exception.message)
        self.assertEqual(ctx.exception.url, self.URL)

    def test_rejects_other_formats(self):
        self._serve(_image_bytes((1200, 627), "GIF"))
        with self.assertRaises(InvalidCertificateBackground) as ctx:
            self.validator.execute([self.URL])
        self.assertIn("GIF", ctx.exception.message)

    def test_rejects_empty_background(self):
        for value in ("", "   "):
            with self.assertRaises(InvalidCertificateBackground) as ctx:
                self.validator.execute([value])
            self.assertIn("não informado", ctx.exception.message)
        self.client.get.assert_not_called()

    def test_rejects_unreachable_url(self):
        self._serve(b"not found", status_code=404)
        with self.assertRaises(InvalidCertificateBackground) as ctx:
            self.validator.execute([self.URL])
        self.assertIn("Não foi possível baixar", ctx.exception.message)

    def test_rejects_content_that_is_not_an_image(self):
        self._serve(b"<html>login</html>")
        with self.assertRaises(InvalidCertificateBackground):
            self.validator.execute([self.URL])

    def test_downloads_each_distinct_url_once(self):
        self._serve(_image_bytes((1200, 627)))
        self.validator.execute([self.URL, self.URL, self.URL])
        self.assertEqual(self.client.get.call_count, 1)


if __name__ == "__main__":
    unittest.main()
