import configparser
from KalturaClient import *
from KalturaClient.Plugins.Core import *
import xlsxwriter
import requests
import os
from PIL import Image

(CONF_FILE, KALTURA, PARTNER_ID, USER_ID, ADMIN_SECRET, CATEGORY_ID, LINK, OEMBED, EMBED_CODE, SERVICE_URL) = [
    "config.ini", "KALTURA", "PARTNER_ID", "USER_ID", "ADMIN_SECRET", "CATEGORY_ID", "LINK", "OEMBED", "EMBED_CODE", "https://www.KALTURA.com/"]

conf = {}
client = {}
excel = {'wb': None, 'ws': None}


def init_conf(fn):
    ret = configparser.ConfigParser()
    ret.read(fn)
    return ret


def init_kaltura(conf):
    config = KalturaConfiguration(conf[KALTURA][PARTNER_ID])
    config.serviceUrl = SERVICE_URL
    retclient = KalturaClient(config)
    ks = retclient.session.start(
        conf[KALTURA][ADMIN_SECRET],
        conf[KALTURA][USER_ID],
        KalturaSessionType.ADMIN,
        conf[KALTURA][PARTNER_ID])
    retclient.setKs(ks)
    return retclient


def get_category_name(kc, catId):
    result = kc.category.get(catId)
    return result.name


def get_thumb(url, filename):
    with open(filename, 'wb') as handle:
        response = requests.get(url, stream=True)
        if not response.ok:
            print('getThumb url=', url, 'filename=',
                  filename, 'response=', response)
        for block in response.iter_content(1024):
            if not block:
                break
            handle.write(block)


def init_excel(conf, client):
    workbook = xlsxwriter.Workbook(conf[KALTURA][PARTNER_ID]+'.xlsx')
    worksheet = workbook.add_worksheet(
        get_category_name(client, conf[KALTURA][CATEGORY_ID])+' '+conf[KALTURA][CATEGORY_ID])
    bold = workbook.add_format({'bold': 1})
    worksheet.write('A1', 'THUMBNAIL', bold)
    worksheet.write('B1', 'ENTRY_ID', bold)
    worksheet.write('C1', 'NAME', bold)
    worksheet.write('D1', 'LINK', bold)
    worksheet.write('E1', 'OEMBED', bold)
    worksheet.write('F1', 'EMBED_CODE', bold)
    worksheet.set_column(0, 0, 22.4)
    worksheet.set_column(1, 1, 10)
    worksheet.freeze_panes(1, 0)
    return (workbook, worksheet)


def kaltura_to_excel(conf, kc, xl):
    filter = KalturaBaseEntryFilter()
    filter.categoriesIdsMatchAnd = conf[KALTURA][CATEGORY_ID]
    pager = KalturaFilterPager()
    pager.setPageSize(30)

    (row,maxx,maxy,maxc,curPage) = (2,120.0,68.0,0,0)
    
    while True:
        curPage += 1
        print('page', curPage)
        pager.setPageIndex(curPage)
        result = kc.baseEntry.list(filter, pager)
        if len(result.objects) == 0:
            break
        for curEntry in result.objects:
            thumb = 'thumbnails/'+curEntry.id+'.jpeg'
            get_thumb(curEntry.thumbnailUrl, thumb)
            fileSize = os.stat(thumb).st_size
            if fileSize > 0:
                img = Image.open(thumb)
                (x, y) = img.size
                scale = min(maxx/x, maxy/y)
                if scale < 1:
                    img = img.resize((int(x*scale), int(y*scale)))
                    img.save(thumb, 'JPEG')
                    print(thumb, 'resized')
                else:
                    img = img.resize((x, y))
                    img.save(thumb, 'JPEG')
                    print(thumb, '--saved--')
                xl['ws'].insert_image(
                    'A'+str(row), thumb, {'x_offset': 2, 'y_offset': 2, 'object_position': 1, 'x_scale': 1.1, 'y_scale': 1.1})
                xl['ws'].set_row(row-1, 72)
            else:
                xl['ws'].write('A'+str(row), 'no thumbnail')
                xl['ws'].set_row(row-1, 10)
            xl['ws'].write('B'+str(row), curEntry.id)
            xl['ws'].write('C'+str(row), curEntry.name)
            maxc = max(maxc, len(curEntry.name))
            xl['ws'].write_url(
                'D'+str(row), conf[KALTURA][LINK]+curEntry.id, string='link')
            xl['ws'].write_string(
                'E'+str(row), conf[KALTURA][OEMBED].replace('ENTRY_ID', curEntry.id))
            xl['ws'].write_string(
                'F'+str(row), conf[KALTURA][EMBED_CODE].replace('ENTRY_ID', curEntry.id))
            row += 1

    xl['ws'].set_column(2, 2, int(maxc*0.85))


def close_stuff(xl, kc):
    xl['wb'].close()
    kc.session.end()


conf = init_conf(CONF_FILE)
client = init_kaltura(conf)
(excel['wb'], excel['ws']) = init_excel(conf, client)
kaltura_to_excel(conf, client, excel)
close_stuff(excel, client)
