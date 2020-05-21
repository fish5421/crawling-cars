#! /usr/bin/env python3
import scrapy
from tesla_price.items import TeslaPriceItem
import numpy as np
import re
import requests
import scrapy_crawlera


from scrapy.http import HtmlResponse


class Cars(scrapy.Spider):
    name = 'cars_spider'
    allowed_urls = ['https://www.cars.com/']
    start_urls = ['https://www.cars.com/for-sale/searchresults.action/?mkId=28263&page=1&perPage=100&rd=99999&searchSource=PAGINATION&sort=relevance&yrId=58487%2C30031936%2C35797618%2C36362520%2C36620293&zc=20005']
    BASE_URL = 'https://www.cars.com'

    def parse(self, response):
        # num_of_results = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "filter-count", " " ))]//text()').get()
        number_of_pages = response.xpath('//li[(((count(preceding-sibling::*) + 1) = 7) and parent::*)]//*[contains(concat( " ", @class, " " ), concat( " ", "not-current", " " ))]//text()').get()
        # print(number_of_pages)
        # num_of_cars_per_page = 100
        # num_int = int(num_of_results)

        # if num_int % num_of_cars_per_page == 0:
        #     total_pages = num_int//num_of_cars_per_page
        #
        # else:
        #     total_pages = num_int//num_of_cars_per_page + 1
        total_pages = number_of_pages

        tesla_urls = [f"https://www.cars.com/for-sale/searchresults.action/?dealerType=localOnly&mkId=28263&page={i}&perPage=100&rd=99999&searchSource=GN_REFINEMENT&sort=relevance&yrId=58487%2C30031936%2C35797618%2C36362520%2C36620293&zc=20005" for i in range(1, total_pages)]
        for url in tesla_urls:
            yield scrapy.Request(url, callback=self.parse_results)

    def parse_results(self, response):
        url = 'https://www.cars.com/for-sale/searchresults.action/?dealerType=localOnly&mkId=28263&page=1&perPage=100&rd=99999&searchSource=GN_REFINEMENT&sort=relevance&yrId=58487%2C30031936%2C35797618%2C36362520%2C36620293&zc=20005'
        resp = requests.get(url)
        response = HtmlResponse(url="", body=resp.text, encoding='utf-8')
        print(response)
        links = response.xpath('//*[@id="srp-listing-rows-container"]/div[@class="shop-srp-listings__listing-container"]')
        for i,link in enumerate(links):
            ext_color = ' '.join([str(elem) for elem in link.css('.listing-row__meta li:nth-of-type(1)::text').getall()]).replace('\n', '').strip()   
            int_color = ' '.join([str(elem) for elem in link.css('.listing-row__meta li:nth-of-type(2)::text').getall()]).replace('\n', '').strip()  
            # try:
            #     price = link.xpath('.//span[@class="listing-row__price "]/text()').extract_first().strip().replace('$','').replace(',','')
            # except AttributeError:
            #     price = link.xpath('.//span[@class="listing-row__price new"]/text()').extract_first().strip().replace('$','').replace(',','')
            try:
                ori_price = link.xpath('.//span[@class="listing-row__old-price"]/text()').extract_first().strip().replace('$','').replace(',','')
            except AttributeError:
                ori_price = np.nan
            drive_train = ' '.join([str(elem) for elem in link.css('.listing-row__meta li:nth-of-type(4)::text').getall()]).replace('\n', '').strip()     

            detail_url = response.xpath('//@data-goto-vdp')[i].get() 
            absolute_url = self.BASE_URL + f'/vehicledetail/detail/{detail_url}/overview/'
            yield scrapy.Request(absolute_url, callback=self.parse_attr,
                                 meta={
                                     #'price': price,
                                     'ori_price': ori_price,
                                     'ext_color': ext_color,
                                     'int_color': int_color,
                                     'drivetrain': drive_train,
                                     'url': absolute_url
                                 })

    def parse_attr(self, response):
        self.logger.info('Parse function called on %s', response.url)
        item = TeslaPriceItem()
        # price = response.meta['price']
        ori_price = response.meta['ori_price']
        ext_color = response.meta['ext_color']
        int_color = response.meta['int_color']
        drive_train = response.meta['drivetrain']
        url = response.meta['url']

        price = response.css('span.vehicle-info__price-display::text').extract_first().strip().replace('$','').replace(',','')

        # year_1 is being used to get the year, make and model out of a single listing for cars.com
        year_1 = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "vehicle-info__title", " " ))]//text()').getall()

        # year_and_model_remove_from_list will remove the string from the list so that you can adjust the actual string
        year_and_model_remove_from_list =  year_1[0]

        # Formatting used to remove the white spaces from the string
        year_only_remove_white_spaces =  year_and_model_remove_from_list.strip()[0:4]

        # Add the year to the item
        #item["year"] =  year_only_remove_white_spaces
        year = year_only_remove_white_spaces

        # model_1 will be the model
        model_1 = year_and_model_remove_from_list[5:].replace('Tesla', '').strip()[:7]   
        model = model_1

        # Configuration will take out all the Tesla and Model info and leave config and battery
        #item["configuration"] = year_and_model_remove_from_list[5:].replace('Tesla', '').strip()[7:].strip()
        configuration = year_and_model_remove_from_list[5:].replace('Tesla', '').strip()[7:].strip()

        # Grabbing the notes from the seller
        notes_from_seller = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "details-section__seller-notes", " " ))]//text()').getall() 

        # Formatting to remove from the list and remove spaces
        notes_from_seller_remove_from_list = ' '.join([str(elem) for elem in notes_from_seller]).strip()
        notes_from_seller_formatted = notes_from_seller_remove_from_list.replace('\n', '')

        autopilot = re.findall(r"(?i)(autopilot)", notes_from_seller_formatted)
        if len(autopilot) > 0:
            autopilot = True
        else:
            autopilot = False


        # If statement to check for the works original in the notes and make sure something was found before adding to items
        if 'Original' or 'original' in notes_from_seller_formatted:
            match = re.search(r"([$](?:\d{2}|\d{3})(,)\d{3})", notes_from_seller_formatted) 
            if match != None:
                original = match.group(0)
            else: 
                original = notes_from_seller_formatted

        else:
            original = notes_from_seller_formatted

        deal_for_car = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "vehicle-info__market-comparison", " " ))]//text()').getall()  
        
        try:
            deal = deal_for_car[2] + deal_for_car[3]
        except IndexError:
            deal = np.nan
        
        miles_formatted = response.css('div.vdp-cap-price__mileage--mobile::text').get()
        miles_formatted = miles_formatted.replace('miles', '').strip().replace(',','')

        sold_by = response.css('div.page-section--seller-details h2.page-section__title::text').get()
        dealer_zip_code = response.xpath('.//div[@class="get-directions-link seller-details-location__text"]/a/text()').extract_first()
        try: 
            dealer_zip_code = re.findall(r"\d{5}",dealer_zip_code)
        except TypeError:
            dealer_zip_code = np.nan

        dealer_rating = response.css('div.rating__seller-details-top--reviews-text p.rating__link::text').get()
        try:
            match = re.search(r"\d(.)\d", dealer_rating)
            if match != None:
                dealer_rating = match.group(0)
            else:
                dealer_rating = np.nan
        except TypeError:
            dealer_rating = np.nan

        num_dealer_reviews = response.css('a.rating__link--has-reviews-count::text').get()
        try:
            num_dealer_reviews = re.findall(r"\d+", num_dealer_reviews)
        except TypeError:
            num_dealer_reviews = np.nan
        good_deal = response.xpath('//*[contains(concat( " ", @class, " " ), concat( " ", "good-deal-price", " " ))]//text()').get()
        try:
            good_deal = good_deal.strip().replace("$", "").replace(',','')

        except AttributeError:
            good_deal = np.nan
        
        try:
            vin = "".join(response.xpath('.//li[@class="vdp-details-basics__item"]//text()').extract())
            vin = re.findall('(?<=VIN: ).*',vin)[0].strip()
        except IndexError:
    	    vin = np.nan

        hot_or_not = response.css('.hot-badge--label strong').get()
        if hot_or_not:
            hot_or_not = True
        else:
            hot_or_not = False

        item["year"] = year
        item["model"] = model
        item["configuration"] = configuration
        item["autopilot"] = autopilot
        item["notes_from_seller"] = original
        item["deal"] = deal
        item["mileage"] = miles_formatted
        item["sold_by"] = sold_by
        item["location"] = dealer_zip_code
        item["rating"] = dealer_rating
        item["number_of_reviews"] = num_dealer_reviews
        item["good_deal_margin"] = good_deal
        item["hot_car"] = hot_or_not
        item["vin"] = vin
        item["ext_color"] = ext_color
        item["int_color"] = int_color
        item["price"] = price
        item["original_price"] = ori_price
        item["drive_train"] = drive_train
        item["url"] = url
        item["price"] = price

        yield item
