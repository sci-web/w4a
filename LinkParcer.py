import getopt, re, sys
from BeautifulSoup import BeautifulSoup

def parse(html):
    digest = html[html.find("<br>"):]
    digest = digest[4:]
    html = BeautifulSoup(html)
    title = html.a.string
    link = html.a.href
    pr_info = title[title.find("(")+1:title.find(")")]
    authors, date, place = pr_info.split(", ")
    title =  title[0:title.find("(")]
    print 
    print "\"Title\": \"" + title + "\","
    print "\"Link\": \"" + html.a['href'] + "\","
    print "\"InfoDate\": \"" + date + "\""
    print "\"InfoAuthors\": \"" + authors + "\","
    print "\"InfoPlace\": \"" + place + "\","
    print "\"Digest\": \"" + digest + "\","

def main(argv):
    try:
        opts, arg = getopt.getopt(argv, "t:", ["txt="])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        arg.rstrip("\n\r")
        if opt in ("-t", "--txt"):
            parse(arg)
        else:
            print "no HTML input"

if __name__ == '__main__':
    main(sys.argv[1:])
