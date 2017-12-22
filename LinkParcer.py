# -*- coding: UTF-8 -*-
import getopt, re, sys
from BeautifulSoup import BeautifulSoup


def parse(html):
    num = html[0:html.find(".")]
    digest = html[html.find("<br>"):]
    digest = digest[4:]
    soup = BeautifulSoup(html)
    try:
        title = soup.a.string
        link = soup.a.href
    except:
        title = ""
        link = ""
    pr_info = title[title.rfind("(")+1:title.rfind(")")]
    dt = ["","",""]
    if title.find("(") > 0:
        dt = pr_info.split(", ")        # authors, date, place
        title =  title[0:title.find(" (")]
        link = soup.a['href']
    else:
        digest = html
        title = ""
        link = ""
    inner = BeautifulSoup(digest)
    pattern =r'<(a|/a).*?>'    
    for a in inner.findAll('a', href=True):
        try:
            lnk = "[" + a.string + "==" + a['href'] + "]"
            digest = re.sub(pattern, "*", digest)
            digest = digest.replace("*"+str(a.string)+"*", lnk.encode('utf-8'))
        except: 
            print a.string
    print "    {"
    print "        \"num\": " + num + ","    
    print "        \"title\": \"" + title + "\","
    print "        \"link\": \"" + link + "\","
    print "        \"info_type\": \"article\","
    print "        \"info_date\": \"" + dt[1] + "\","
    print "        \"info_authors\": \"" + dt[0] + "\","
    print "        \"infoID\": \"\","
    print "        \"info_place\": \"" + dt[2] + "\","
    print "        \"digest\": \"" + digest + "\""
    print "    },"


def main(argv):
    try:
        opts, arg = getopt.getopt(argv, "t:", ["txt="])
    except getopt.GetoptError:
        sys.exit(2)
    if len(opts) > 0:
        for opt, arg in opts:
            if opt in ("-t", "--txt") and arg:
                arg.rstrip("\n\r")
                parse(arg)
            else:
                print "no HTML input"
    else:
        for point in sys.stdin.read().split("\n\n"):
            point.rstrip("\n\r") 
            parse(point)


if __name__ == '__main__':
    main(sys.argv[1:])
