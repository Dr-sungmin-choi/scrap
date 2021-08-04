from datetime import date, datetime
import argparse
import logging
import logging.handlers
from worker import SimpleWorker


### Log setting
# sys.tracebacklimit=0
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
log.addHandler(stream_handler)

def is_valid(args):
    '''
    check whether the arguments are valid.
    What does it check:
        1) total: keyword(required)
        2) process: input_path(required)
        3) end_date > start_date
    '''
    if not args.keyword and args.mode == 'total':
        raise ValueError('No keyword to query. Please specify a keyword.')
    elif not args.input_path and args.mode =='process':
        raise ValueError('You should specify the file name to process.')
    elif datetime.strptime(args.start_date, '%Y%m%d') > datetime.strptime(args.end_date, '%Y%m%d'):
        raise ValueError('The date is invalid. Please fill the correct date.')
    return True

def get_argument():
    '''
    parse the defined arguments from sys.argv
    Argument list:
        1) keyword(scrap & total required)
        2) start_date
        3) end_date
        4) limit
        5) input_path(process required)
        6) mode
        7) period
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', type=str, help='A Single keyword to query')
    parser.add_argument('--start_date', type=str, default=date.today().strftime('%Y%m%d'), help='Start date for querying')
    parser.add_argument('--end_date', type=str, default=date.today().strftime('%Y%m%d'), help='End date for querying')
    parser.add_argument('--limit', type=int, default=10000, help='The number of sources to scrap. Default is 1.')
    parser.add_argument('--input_path', type=str, help='Path of the file which contains source text')
    parser.add_argument('--mode', type=str, default='total', help='Total, process, or scrap')
    parser.add_argument('--period', type=str, default=None, help='Analysis period. y, 6m') ## TODO
    args = parser.parse_args()
    return args

def run():
    log.info('Creating workers...')
    if args.period is None:
        periods = [(args.start_date, args.end_date)]
    else:
        periods = list()
    worker = SimpleWorker(
        keyword=args.keyword, 
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
