import configparser
from KalturaClient import *
from KalturaClient.Plugins.Core import *

conf = configparser.ConfigParser()
(CONF_FILE, KALTURA, PARTNER_ID, USER_ID, ADMIN_SECRET, CATEGORY_ID, SERVICE_URL) = [
    "config.ini", "KALTURA", "PARTNER_ID", "USER_ID", "ADMIN_SECRET", "CATEGORY_ID", "https://www.KALTURA.com/"]
conf.read(CONF_FILE)

config = KalturaConfiguration(conf[KALTURA][PARTNER_ID])
config.serviceUrl = SERVICE_URL
client = KalturaClient(config)
ks = client.session.start(
    conf[KALTURA][ADMIN_SECRET],
    conf[KALTURA][USER_ID],
    KalturaSessionType.ADMIN,
    conf[KALTURA][PARTNER_ID])
client.setKs(ks)

filter = KalturaBaseEntryFilter()
filter.categoriesIdsMatchAnd = conf[KALTURA][CATEGORY_ID]
pager = KalturaFilterPager()

result = client.baseEntry.list(filter, pager)
for curEntry in result.objects:
    print(curEntry.id,curEntry.name)
