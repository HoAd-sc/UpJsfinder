import requests, argparse, sys, re
from requests.packages import urllib3
from urllib.parse import urlparse
from bs4 import BeautifulSoup


#定义 获取参数函数
def parse_args():
    parser = argparse.ArgumentParser(epilog='\tExample: \r\npython ' + sys.argv[0] + " -u http://www.baidu.com")
    parser.add_argument("-u", "--url", help="The website")
    parser.add_argument("-c", "--cookie", help="The website cookie")
    return parser.parse_args()
#d定义 发送网络请求包
def request_url(url):
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36",
        "Cookie": "args.cookie"}
    try:
        raw = requests.get(url, headers=header, timeout=3, verify=False)
        raw = raw.content.decode("utf-8", "ignore")
        return raw
    except:
        return None
#通过正则来匹配出需要的东西
def re_check(js):
	pattern_raw = r"""
      (?:"|')                               # Start newline delimiter
      (
        ((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
        [^"'/]{1,}\.                        # Match a domainname (any character + dot)
        [a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path
        |
        ((?:/|\.\./|\./)                    # Start with /,../,./
        [^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
        [^"'><,;|()]{1,})                   # Rest of the characters can't be
        |
        ([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
        [a-zA-Z0-9_\-/]{1,}                 # Resource name
        \.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
        (?:[\?|/][^"|']{0,}|))              # ? mark with parameters
        |
        ([a-zA-Z0-9_\-]{1,}                 # filename
        \.(?:php|asp|aspx|jsp|json|
             action|html|js|txt|xml|do|
             word|pdf)             # . + extension
        (?:\?[^"|']{0,}|))                  # ? mark with parameters
      )
      (?:"|')                               # End newline delimiter
    """
	pattern = re.compile(pattern_raw, re.VERBOSE)
	result = re.finditer(pattern, str(js))
	if result == None:
		return None
	js_url = []
	return [match.group().strip('"').strip("'") for match in result
			if match.group() not in js_url]

#对正则出来的url或者路径进行匹配拼接
def make_url(url, re_URL):
	black_url = ["javascript:"]	# Add some keyword for filter url.
	URL_raw = urlparse(url)
	domain_URL = URL_raw.netloc #域名
	protocol_URL = URL_raw.scheme #协议 https http
	if re_URL[0:2] == "//":
		result = protocol_URL  + ":" + re_URL
	elif re_URL[0:4] == "http":
		result = re_URL
	elif re_URL[0:2] != "//" and re_URL not in black_url:
		if re_URL[0:1] == "/":
			result = protocol_URL + "://" + domain_URL + re_URL
		else:
			if re_URL[0:1] == ".":
				if re_URL[0:2] == "..":
					result = protocol_URL + "://" + domain_URL + re_URL[2:]
				else:
					result = protocol_URL + "://" + domain_URL + re_URL[1:]
			else:
				result = protocol_URL + "://" + domain_URL + "/" + re_URL
	else:
		result = url
	return result
def find_last(string,str):
	positions = []
	last_position=-1
	while True:
		position = string.find(str,last_position+1)
		if position == -1:break
		last_position = position
		positions.append(position)
	return positions
def find_subdomain(urls, mainurl):
	url_raw = urlparse(mainurl)
	domain = url_raw.netloc
	miandomain = domain
	positions = find_last(domain, ".")
	if len(positions) > 1:miandomain = domain[positions[-2] + 1:]
	subdomains = []
	for url in urls:
		suburl = urlparse(url)
		subdomain = suburl.netloc
		#print(subdomain)
		if subdomain.strip() == "": continue
		if miandomain in subdomain:
			if subdomain not in subdomains:
				subdomains.append(subdomain)
	return subdomains
def giveresult(urls, domian):
	if urls == None:
		return None
	print("Find " + str(len(urls)) + " URL:")
	content_url = ""
	content_subdomain = ""
	for url in urls:
		content_url += url + "\n"
		print(url)
	subdomains = find_subdomain(urls, domian)
	print("\nFind " + str(len(subdomains)) + " Subdomain:")
	for subdomain in subdomains:
		content_subdomain += subdomain + "\n"
		print(subdomain)
#主要处理url函数
def re_by_url(url,js=False):
	if js == False:
		html_raw = request_url(url)
		if html_raw == None:
			print("Fail to access " + url)
			return None
		html = BeautifulSoup(html_raw, "html.parser")
		html_scripts = html.findAll("script")
		html_forms = html.findAll("form")
		html_links = html.findAll("link")
		script_array = {}
		script_temp = ""
		for html_script in html_scripts:
			if html_script.get("src") == None:
				pass
			else:
				script_src = html_script.get("src")
				purl = make_url(url, script_src)
				script_array[purl] = request_url(purl)
		for html_form in html_forms:
			if html_form.get("action") == None:
				pass
			else:
				form_action = html_form.get("action")
				purl = make_url(url, form_action)
				script_array[purl] = request_url(purl)
		for html_link in html_links:
			if html_link.get("href") == None:
				pass
			else:
				link_href = html_link.get("href")
				purl = make_url(url, link_href)
				script_array[purl] = request_url(purl)
		script_array[url] = script_temp
		allurls = []
		for script in script_array:
			allurls.append(script)
			temp_urls = re_check(script_array[script])

			if len(temp_urls) == 0: continue
			for temp_url in temp_urls:
				allurls.append(make_url(script, temp_url))

		# print(allurls)
		result = []
		for singerurl in allurls:
			# print(singerurl)
			url_raw = urlparse(url)
			domain = url_raw.netloc
			positions = find_last(domain, ".")
			miandomain = domain
			if len(positions) > 1: miandomain = domain[positions[-2] + 1:]
			# print(miandomain)
			suburl = urlparse(singerurl)
			subdomain = suburl.netloc
			# print(singerurl)
			if miandomain in subdomain or subdomain.strip() == "":
				if singerurl.strip() not in result:
					result.append(singerurl)
		return result
	return sorted(set(re_check(request_url(url)))) or None


if __name__ == '__main__':
	urllib3.disable_warnings()#不报错
	args = parse_args()
	urls = re_by_url(args.url)
	giveresult(urls, args.url)
