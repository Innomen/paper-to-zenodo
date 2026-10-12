"""Metadata parity across the two canonical paper layouts, without network writes."""
import tempfile
import unittest
from pathlib import Path
from zenodo_publish import parse_paper

class MetadataTests(unittest.TestCase):
    def test_frontmatter_and_body_metadata_agree(self):
        layouts = [
            '---\ntitle: "Example: A Paper"\nauthor: "Brandon M. Sergent"\nabstract: |\n  First abstract line.\n  Second abstract line.\n\n  **Keywords:** experience, other minds\n---\n\n## 1. Introduction\nBody.\n',
            '# Example: A Paper\n\n**Brandon M. Sergent**\n\n## Abstract\n\nFirst abstract line.\nSecond abstract line.\n\n**Keywords:** experience, other minds\n\n## 1. Introduction\nBody.\n',
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'paper.md'
            results = []
            for layout in layouts:
                path.write_text(layout)
                results.append(parse_paper(path, '0009-0001-4165-5463', 'Brandon M. Sergent', 'preprint'))
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0]['creators'][0]['name'], 'Sergent, Brandon M.')
        self.assertEqual(results[0]['keywords'], ['experience', 'other minds'])
        self.assertIn('<p>First abstract line. Second abstract line.</p>', results[0]['description'])

if __name__ == '__main__':
    unittest.main()
