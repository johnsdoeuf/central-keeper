import logging
import unittest

class Init_para(unittest.TestCase):
	def test_1(self):
		log = logging.getLogger('tttt')

		with self.assertLogs(logger=log , level=logging.ERROR) as cm:
			log.error('message important')

# Programme principal

if __name__ == '__main__':
	unittest.main()
