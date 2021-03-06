import time
from datetime import date, datetime
import argparse
import logging
import logging.handlers
from worker import Worker, SimpleWorker

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
    # elif not osp.isfile(args.output_path):
    #     raise ValueError('File output is a directory, will not save outputs to the file.')
    # if not args.query and not args.keyword_file:
        # raise ValueError('No keywords to query. Please provide either an keyword file or specify a single keyword.')
    # if args.query and args.keyword_file:
        # raise ValueError('You should use only one argument either a single keyword or an keyword_file')
    # elif args.keyword_file and not osp.exists(args.keyword_file):
        # raise FileNotFoundError("Keyword file doesn't exist at {}".format(args.keyword_file))
    return True

def get_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', type=str, help='A Single keyword to query')
    # parser.add_argument('--keyword_file', type=str, help='Path of the File which contains Keywords to Search for')
    parser.add_argument('--start_date', type=str, default=date.today().strftime('%Y%m%d'), help='Start date for querying')
    parser.add_argument('--end_date', type=str, default=date.today().strftime('%Y%m%d'), help='End date for querying')
    parser.add_argument('--limit', type=int, default=1, help='The number of sources to scrap. Default is 1.')
    parser.add_argument('--input_path', type=str, help='Path of the file which contains source text')
    # parser.add_argument('--output_path', type=str, default='./output/output.txt', help='Path of the file which will save the result of querying')
    parser.add_argument('--mode', type=str, default='total', help='Total, process, or scrap')
    parser.add_argument('--model_set', type=str, default='base', helper='Processing complexity')
    args = parser.parse_args()
    return args

def run():
    log.info('Creating workers...')
    # _queries = args.query if args.query else args.keyword_file
    worker = Worker(
            keyword=args.query, 
            start_date=args.start_date,
            end_date=args.end_date,
            limit=args.limit,
            # output_path=args.output_path,
            mode=args.mode,
            model_set=args.model_set,
            input_path=args.input_path
    )
    worker.run()

if __name__ == '__main__':    
    args = get_argument()
    if is_valid(args):
        log.info('Checking arguments completed.')
        run()
    else:
        raise ValueError('Invalid arguments. See help with --h if you need')
