import unittest
from PIL import Image
from srp.vision import combine, crop, match_name

class VisionTests(unittest.TestCase):
    def test_alias(self):
        self.assertEqual(match_name('大嘴鸥', {'Pelipper':['大嘴鸥']})[0]['species'], 'Pelipper')
        self.assertEqual(match_name('', {'Pelipper':['大嘴鸥']}), [])
    def test_conflict(self):
        self.assertIsNone(combine([{'species':'A','score':0.9}], [{'species':'B','score':0.9}])[0])
    def test_bounds(self):
        with self.assertRaises(ValueError):
            crop(Image.new('RGB',(10,10)), [9,9,5,5])
