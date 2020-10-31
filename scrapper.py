import requests
from bs4 import BeautifulSoup
import smtplib

URL = 'INSERT_URL_YANG_MAU_DISCRAPPING'

headers = {"User-Agent": 'SEARCH_GOOGLE_USER-AGENT_MY_COMPUTER'} 
#contoh user-agent : Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36 OPR/62.0.3331.116

class TokopediaScraper(Scraper):
    def __init__(self, headers=HEADERS, debug=False):
        super(TokopediaScraper, self).__init__()
        self.headers = {**self.headers, **headers}
        self.url_products = [
            'https://www.tokopedia.com/bennykoicikarang/lenovo-yoga-900',
            'https://www.tokopedia.com/toptech/hp-14-cm0091au-amd-a4-9125-ssd-128gb-4gb-win10-joy-2'
        ]
        self.debug = debug
        self.data_detail_products = []

    def getDataByClass(self, content, name, as_text=True):
        """Get Data by Class Name
        """
        data = content.find(attrs={'class': name})
        if as_text and data:
            return data.text.strip()
        return data

    def getDataByProp(self, content, name, as_text=True, strip=True):
        """Get Data by Prop Name
        """
        data = content.find(attrs={'itemprop': name})
        resp = None
        if data:
            if as_text and strip:
                resp = data.text.strip()
            elif as_text and not strip:
                content = "".join([str(item).strip() for item in data.contents])
                resp = content
            else:
                resp = data
        return resp

    def getDataByAttr(self, content, attr={}, type='value', default=None):
        """ Get Data by Attr """
        data = content.find(attrs=attr)
        resp = default
        if data:
            if type == 'value':
                resp = data['value']
            elif type == 'text':
                resp = data.text.strip()
            else:
                resp = data
        return resp

    def getDataValue(self, content, name, selector=getDataByProp, as_text=True, strip=True):
        """Get Value Data.
        """
        # TODO: Add option to use `selector` so it's make more flexible
        data = self.getDataByProp(content, name, as_text, strip)
        return data

    def getListUrl(self, offset=0, limit=100):
        """Get List URLs from default category.

        :param offset: Offset of category page
        :param limit: Limit data to show
        :return: list of (cleaned) product url
        """
        url_category = f"https://ace.tokopedia.com/search/product/v3?scheme=https&device=desktop&related=true&start={offset}&ob=23&source=directory&st=product&identifier=laptop-aksesoris_laptop&sc=289&rows={limit}&unique_id=7164647f8d9d4c9798da21c416b76558&safe_search=false"
        req = self.openURL(url_category)
        urls = []
        if req:
            result = req.json()
            products = result.get('data').get('products')
            for product in products:
                product_url = product.get('url')
                if product_url:
                    cleaned_url = product_url.split('?')[0]
                    urls.append(cleaned_url)
        return urls

    def setListUrl(self, urls):
        """Set List of URL Product to scrape """
        if isinstance(urls, list) or isinstance(urls, tuple):
            self.url_products = urls
        else:
            print("[-] URL is not valid list or tuple!")
            # Set to empty if urls not valid
            self.url_products = []

    def extractProductDetail(self, url):
        soup = self.getPage(url)
        tokped = TokopediaData()
        tokped.id = self.getDataByAttr(soup, attr={'name': 'product_id'}, default=0)
        tokped.title = self.getDataValue(soup, 'name')
        tokped.description = self.getDataValue(soup, 'description', strip=False)
        tokped.price = self.getDataByAttr(soup, {'id': 'product_price_int'})

        if self.debug:
            tokped.display()

        return tokped

    def run(self):
        """Run Scraper """
        products = []
        for url in self.url_products:
            product = self.extractProductDetail(url)
            products.append(product.toList())
        self.data_detail_products = products

    def saveData(self, path='data_products.csv'):
        """Save data products to file """
        with open(path, 'w') as file:
            writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
            writer.writerow(['id', 'product_id', 'title', 'description', 'price'])
            index = 0
            for data in self.data_detail_products:
                index += 1
                writer.writerow([index, data[0], data[1], data[2], data[3]])

            print(f"Data saved to `{path}`")

def check_price():
    page = requests.get(URL, headers=headers)

    soup = BeautifulSoup(page.content, 'html.parser') 
    #fungsi html.parser berguna untuk mempermudah kita untuk membaca code

    title = soup.h1.get_text() 
    #kita harus inspect element dan klik bagian judul nya, jadi tiap e-commerce yang digunakan bisa berbeda-beda

    price = float(soup.find("span", itemprop="price").get_text())
    #inspect element dan klik bagian harganya

    print(title.strip())
    print(price)
    
    #Jika barang dibawah 300k maka akan mengirim email menggunakan method send_mail()
    if(price < 300000):
        send_mail()
    
def send_mail():
    server = smtplib.SMTP('smtp.gmail.com', 587) #587 adalah port
    #disini saya menggunakan smtp gmail, apabila kalian tidak menggunakan gmail silahkan cari saja di google smtp list
    
    #disini peran TCP 3-Way Handshake Process mulai bergerak
    server.ehlo()
    server.starttls()
    server.ehlo()
    
    server.login('EMAIL', 'PASSWORD')
    #saya sarankan gunakan fitur Google App Password, karena ada fitur Two-Factor Authentication
    
    subject = "Barang sedang diskon!!"
    body = "Cek barangnya di [insert URL]"
    
    msg = f"Subject: {subject}\n\n{body}"
    
    server.sendmail(
        'PENGIRIM_EMAIL',
        'PENERIMA_EMAIL',
        msg
    )
    
    print("Email sudah terkirim")
    server.quit()


check_price()


class TokopediaData:
    def __init__(self, productId=None, title=None, description=None, price=0):
        self.id = productId
        self.title = title
        self.description = description
        self.price = price

    def display(self):
        print(f"ProductID: {self.id}")
        print(f"Title: {self.title}")
        print(f"Description: {self.description}")
        print(f"Price: {self.price}")

    def toList(self):
        data = [
            self.id,
            self.title,
            self.description,
            self.price
        ]
        return data

    def toDict(self):
        data_dict = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': self.price
        }
        return data_dict
