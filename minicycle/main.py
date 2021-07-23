import time
from datetime import date, datetime
import argparse
import logging
import logging.handlers
from worker import SimpleWorker

# sys.tracebacklimit=0
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
log.addHandler(stream_handler)

def is_valid(args):
    if not args.query and args.mode == 'total':
        raise ValueError('No keyword to query. Please specify a keyword.')
    elif not args.input_path and args.mode =='process':
        raise ValueError('You should specify the file name to process.')
    elif datetime.strptime(args.start_date, '%Y%m%d') > datetime.strptime(args.end_date, '%Y%m%d'):
        raise ValueError('The date is invalid. Please fill the correct date.')
    return True

def get_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, help='A Single keyword to query')
    parser.add_argument('--start_date', type=str, default=date.today().strftime('%Y%m%d'), help='Start date for querying')
    parser.add_argument('--end_date', type=str, default=date.today().strftime('%Y%m%d'), help='End date for querying')
    parser.add_argument('--limit', type=int, default=10000, help='The number of sources to scrap. Default is 1.')
    parser.add_argument('--input_path', type=str, help='Path of the file which contains source text')
    parser.add_argument('--mode', type=str, default='total', help='Total, process, or scrap')
    parser.add_argument('--period', type=str, default=None, help='Analysis period.') ## TODO
    args = parser.parse_args()
    return args

def run():
    log.info('Creating workers...')
    if args.period is None:
        periods = [(args.start_date, args.end_date)]
    else:
        periods = list()
    worker = SimpleWorker(
        keyword=args.query, 
        start_date=args.start_date,
        end_date=args.end_date,
        limit=args.limit,
        # output_path=args.output_path,
        mode=args.mode,
        input_path=args.input_path
    )
    worker.run()

if __name__ == '__main__':
    log.info('Checking arguments...')    
    args = get_argument()
    if is_valid(args):
        log.info('Checking arguments completed.')
        run()
    else:
        raise ValueError('Invalid arguments. See help with --h if you need')
