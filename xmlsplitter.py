# import xml.etree.ElementTree as ET

# context = ET.iterparse('test_data.xml', events=('end', ))
# for event, elem in context:
#     print(" inside context",elem)
#     if elem.tag == 'page':
#         print(" inside if page")
#         t = elem.find('title').text
#         filename = format(t + ".xml")
#         with open(filename, 'wb') as f:
#             print(" inside write in file")
#             f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
#             f.write("<root>\n")
#             f.write(ET.tostring(elem))
#             f.write("</root>")


import re

regex = r"\[\[Category:(.*?)\]\]"

test_str = ("The [[Tulane Green Wave football|Tulane Green Wave football team]], representing [[Tulane University]] in the sport of [[American football]] since [[1893 Tulane Olive and Blue football team|1893]], has had 19 players named first-team All-Americans. This includes two players who earned the distinction twice, and one player who was a unanimous selection.&lt;ref name=&quot;Tulane&quot;&gt;{{cite web|url=http://www.tulanegreenwave.com/sports/m-footbl/archive/082010aas.html|title=Tulane All-Americans|publisher=Tulane University Athletics|accessdate=April 23, 2014}}&lt;/ref&gt;"

"==First Team All-Americans=="

"! [[1925 College Football All-America Team|1925]]"
"| [[Peggy Flournoy]]"
"| [[Back (American football)|B]]"

"{{Reflist|2}}"

"{{Tulane Green Wave football navbox}}"

"[[Category:Tulane Green Wave football players|*]]"
"[[Category:Lists of college football All-Americans|Tulane Green Wave]]")

matches = re.finditer(regex, test_str, re.MULTILINE | re.DOTALL)

for matchNum, match in enumerate(matches):
    for groupNum in range(0, len(match.groups())):
        result = match.group(1)
        print (result)