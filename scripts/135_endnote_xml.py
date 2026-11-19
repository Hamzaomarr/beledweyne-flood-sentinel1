import io
from xml.sax.saxutils import escape
recs = [
 ('Continental-Scale Building Detection from High Resolution Satellite Imagery', '2021', 'arXiv', 'https://arxiv.org/pdf/2107.12283'),
 ('Copernicus Data Space Ecosystem | Europe\'s eyes on Earth', '2023', 'Copernicus Data Space Ecosystem', 'https://dataspace.copernicus.eu/'),
 ('UNOSAT', '2022', 'United Nations Satellite Centre', 'https://unosat.org/products/'),
 ('WorldCover | WORLDCOVER', '2020', 'VITO NV', 'https://esa-worldcover.org/'),
 ('Dynamic World - 10m global land cover dataset in Google Earth Engine', '2022', 'Google and the World Resources Institute', 'https://dynamicworld.app/'),
]
x = ['<?xml version="1.0" encoding="UTF-8"?>', '<xml><records>']
for t, y, p, u in recs:
    x.append('<record><ref-type name="Web Page">12</ref-type><titles><title>%s</title></titles><dates><year>%s</year></dates><publisher>%s</publisher><volume>2026</volume><num-vols></num-vols><number>18 November</number><urls><related-urls><url>%s</url></related-urls></urls></record>' % (escape(t), y, escape(p), escape(u)))
x.append('</records></xml>')
open(r'.\Revision\non_doi_sources_endnote.xml', 'w', encoding='utf-8').write('\n'.join(x))
import xml.dom.minidom as m; m.parse(r'.\Revision\non_doi_sources_endnote.xml'); print('xml ok')
