#!/usr/bin/python
'''
@author: qyou

Prequisites:
    <a href='http://lxml.de/'>lxml- XML and HTML with Python </a>
'''
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('investing')

HAS_REQUESTS = False
try:
    import requests
    HAS_REQEUSTS = True
except ImportError:
    pass

import datetime

class DateProcessor(object):
    ''' Process the date information for `PageParser` to use
    '''
    @staticmethod
    def tostr(date):
        '''
        :param date datetime.date
        '''
        assert isinstance(date, datetime.date)
        return date.strftime('%m/%d/%Y')
    @staticmethod
    def get_date_before(daysago):
        '''
        :param daysago int, days before
        '''
        assert isinstance(daysago, int)
        daysdelta = datetime.timedelta(daysago)
        today = datetime.date.today()
        return today - daysdelta    
    
class Period:
    Daily = 'Daily'
    Weekly = 'Weekly'
    Monthly = 'Monthly'
    
class PageParser(object):
    BASE_URL = r'http://www.investing.com/instruments/HistoricalDataAjax'
    USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36'
    METHOD = 'post'
    X_Requested_With = 'XMLHttpRequest'
    Content_Type =  'application/x-www-form-urlencoded' 
    def __init__(self, st_date=None, end_date=None, interval_sec=None, curr_id=None, action=None):
        if interval_sec is None or interval_sec not in (Period.Daily, Period.Weekly, Period.Monthly):
            interval_sec = Period.Daily
        if curr_id is None:
            curr_id = '6408'
        if action is None:
            action = 'historical_data'
        if end_date is None:
            end_date = DateProcessor.tostr(datetime.date.today())
        if st_date is None:
            st_date = DateProcessor.tostr(DateProcessor.get_date_before(30))
        self.postdict = {'action':action,
                         'curr_id':curr_id,
                         'st_date':st_date,
                         'end_date':end_date,
                         'interval_sec':interval_sec}
        self.headers = {
                        'User-Agent': self.USER_AGENT,
                        'Content-Type': self.Content_Type,
                        'X-Requested-With': self.X_Requested_With
                        }
        
    def get_html(self):
        if HAS_REQEUSTS:
            response = requests.request(self.METHOD, self.BASE_URL, headers=self.headers, data=self.postdict)
            if response.status_code == 200:
                return response.text
            else:
                raise requests.exceptions.HTTPError("Not Successfully Respond!")
        else:
            import urllib, urllib2
            payload = urllib.urlencode(self.postdict)
            request = urllib2.Request(self.BASE_URL, headers=self.headers)
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())  
            try:
                response =  opener.open(request, data=payload)
                return response.read()
            except Exception as e:
                raise e
        pass
    def write_to_html(self, htmlstr, filepath=None):
        htmlfilename = "%s-%s-%s" % (self.postdict['st_date'], self.postdict['end_date'], self.postdict['interval_sec'])
        htmldoc = """<!doctype html>
                    <html>
                        <head><title>%s</title></head>
                        <body>
                        <center>%s
                        <hr />created by <a href='mailto:qyou@nlpr.ia.ac.cn'>qyou</center>
                        </body>
                    </html>""" % (htmlfilename, htmlstr)
        if filepath is None:
            filepath = htmlfilename.replace('/', '-') + ".html"
        with open(filepath, 'w') as fout:
            fout.write(htmldoc)
        logger.info("write data to %s" % (filepath,))
        
    def extract_info(self, htmlstr):
        try:
            import lxml.html.soupparser as soupparser
        except ImportError as e:
            logger.error("Import lxml error:"+repr(e))
            raise e
        dom = soupparser.fromstring(htmlstr)
        ths = dom.xpath('div/table/thead/tr/th/text()')
        trs = dom.xpath('div/table/tbody/tr')
        data = []
        for e in trs[:-1]:
            data.append(e.xpath('td/text()'))
        
        statistic_headers = trs[-1].xpath('td/text()')
        statistic_values = trs[-1].xpath('td/span/text()')
        return {'data':{'titles':ths, 'values':data}, 'stats':{'titles':statistic_headers, 'values':statistic_values}} 
               
    def write_to_csv(self, info, csvfilepath=None):
        import csv        
        if csvfilepath is None:
            htmlfilename = "%s-%s-%s" % (self.postdict['st_date'], self.postdict['end_date'], self.postdict['interval_sec'])
            csvfilepath = htmlfilename.replace('/', '-') + ".csv"
        with open(csvfilepath, 'wt') as f:
            writer = csv.writer(f)
            writer.writerow(info['data']['titles'])
            for row in info['data']['values']:
                writer.writerow(row)
        logger.info("write to %s" % (csvfilepath,))
        
def main():
    parser = PageParser(st_date='01/04/2007') # util today
    htmlstr = parser.get_html()
    parser.write_to_html(htmlstr)
    info = parser.extract_info(htmlstr)
    parser.write_to_csv(info)

if __name__ == '__main__':
    main()
