from pathlib import Path
import logging
import sauv

if __name__ == '__main__':
    logging.basicConfig(filename='example.log', level=logging.DEBUG)
    sauv.logger = logging.getLogger()
    src = Path('/media/sauv3T/jeux_home/2020-02-03 20-00_1')
    dst = Path('/media/sauv3T/jeux_home/2020-02-03 21-00_1')

    sauv.fusion_rep(src, dst)
