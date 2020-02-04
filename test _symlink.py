from pathlib import Path
import logging
import sauv

if __name__ == '__main__':
    logging.basicConfig(filename='example.log', level=logging.DEBUG)
    sauv.logger = logging.getLogger()
    src = Path('/home/johannes/temp/1')
    dst = Path('/home/johannes/temp/2')

    sauv.fusion_rep(src, dst)
