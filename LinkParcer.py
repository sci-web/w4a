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
    print "        \"Num\": " + num + ","    
    print "        \"Title\": \"" + title + "\","
    print "        \"Link\": \"" + link + "\","
    print "        \"InfoType\": \"article\","
    print "        \"InfoDate\": \"" + dt[1] + "\","
    print "        \"InfoAuthors\": \"" + dt[0] + "\","
    print "        \"InfoID\": \"\","
    print "        \"InfoPlace\": \"" + dt[2] + "\","
    print "        \"Digest\": \"" + digest + "\""
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
