import json
import time
import pandas as pd
import pymongo
from datetime import datetime
from DrissionPage import ChromiumPage
from parsel import Selector
from pathlib import Path

from scrapy.utils.log import failure_to_exc_info

#TODO:: Mongo Connection string
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "turkishairline_AE_feasiblity"
COLLECTION_OUTPUT = "sample_output1"


#TODO:: Pagesave conection path
try:
    PAGESAVE_PATH = Path("D:/Danesh/turkishairlines_US_feasibility/14_08_2025")
    PAGESAVE_PATH.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(e)


def drission_automation(source,destination,travel_date):
    browser =ChromiumPage()
    browser.clear_cache()
    browser.set.cookies.clear()
    tab = browser.latest_tab
    tab.set.cookies.clear()
    tab.clear_cache()

    price_list_source = []

    date_obj = datetime.strptime(travel_date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%B %d, %Y")

    target_url = "https://www.turkishairlines.com/api/v1/availability"
    tab.listen.start(target_url)
    tab.get("https://www.turkishairlines.com/")

    try:
        time.sleep(3)
        tab.ele('xpath://button[@id="notAllowCookiesButton"]',).click()
    except:pass

    time.sleep(0.5)
    tab.ele('xpath://span[@id="one-way"]',timeout=5).click()

    from_prt = tab.ele('xpath://input[@id="fromPort"]').click()
    from_prt.input(source).click()
    time.sleep(2)
    tab.ele('xpath://ul[@id="bookerInputList"]/li[not(contains(@aria-label,"See all destinations"))]').click()

    from_prt = tab.ele('xpath://input[@id="toPort"]').click()
    from_prt.input(destination).click()
    time.sleep(1.5)
    # tab.wait.ele_displayed('xpath://ul[@id="bookerInputList"]/li')
    tab.ele('xpath://ul[@id="bookerInputList"]/li[not(contains(@aria-label,"See all destinations"))]').click()

    try:
        tab.ele(f'xpath://abbr[@aria-label="{formatted_date}"]',timeout=1).click()
        tab.ele('xpath://button[contains(@class,"RoundAndOneWayTab_okButton")]',timeout=1).click()

    except:
        tab.ele('xpath://span[contains(@class,"style_calendar-placeholder-text")]',timeout=1).click()
        tab.ele(f'xpath://abbr[@aria-label="{formatted_date}"]',timeout=1).click()
        tab.ele('xpath://button[contains(@class,"RoundAndOneWayTab_okButton")]',timeout=1).click()

    tab.ele('xpath://div[contains(@class,"booker-pax-picker-dropdown-cabin-bus")]',timeout=1).click()

    tab.ele('xpath://div[contains(@class,"RoundAndOneWayTab_buttonWrapper")]',timeout=1).click()
    tab.wait.ele_displayed('xpath://div[@class="av__style_flightTitleContainer__bh25l"]')
    time.sleep(1)

    fetch_Product_ID = datetime.now().strftime("%d%m%Y%H%M%S")
    # page_name = f"{fetch_Product_ID}_main.html"
    page_name = f"{fetch_Product_ID}_{source}_{destination}_main.html"
    join_path = PAGESAVE_PATH / page_name

    content = ""
    for i_req in tab.listen.steps():
        response_url = i_req.response.url
        content = i_req.response.body
        status_check = i_req.response.status
        if response_url == target_url and status_check == 200:
            with open(join_path, "w", encoding="utf-8") as f:
                json.dump(content, f, ensure_ascii=False, indent=4)
            break

    elements = tab.eles('xpath://div[contains(@class,"av__FlightItem_flightItemPrice")]')
    for i in range(len(elements)):
        elements = tab.eles('xpath://div[contains(@class,"av__FlightItem_flightItemPrice")]')
        elements[i].click()
        time.sleep(3)
        tab.ele('xpath://div[contains(@class,"style_flightComparisonPackageTable")]//button[contains(@class,"style_thyButton_")]').click()
        time.sleep(5)
        tab.wait.ele_displayed('xpath://a[contains(@class,"av__style_footer-detail-expand")]')
        tab.ele('xpath://a[contains(@class,"av__style_footer-detail-expand")]').click()
        price_source = tab.html
        page_name2 = f"{fetch_Product_ID}_{source}_{destination}_{i+1}_price.html"
        join_path2 = PAGESAVE_PATH / page_name2
        with open(join_path2, "w", encoding="utf-8") as file:
            file.write(price_source)
        price_list_source.append(price_source)
        tab.ele('xpath://a[contains(@class,"av__style_footer-detail-expand")]').click()
        tab.ele('xpath://button[contains(@class,"av__ChangeFlightButton_changeFlightButton")]').click()
        time.sleep(1)
        tab.ele('xpath://span[contains(@class,"av__style_checked")]').click()

    tab.close()
    return content, price_list_source

def convert_minutes(milliseconds):
    seconds = milliseconds // 1000
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if hours and minutes:
        return f"{hours}h {minutes}m"
    elif hours:
        return f"{hours}h"
    else:
        return f"{minutes}m"

# def main(source,destination,travel_date):
def main(source,destination,travel_date,Dep_City,Dep_Country,Destination_Main,Destination_Ticket,Country_Main,Country_Ticket):
    time.sleep(1)
    main_content, price_list_source = drission_automation(source, destination, travel_date)
    mainloop_row = main_content.get("data").get("originDestinationInformationList")[0].get("originDestinationOptionList")

    for subrow, price_ls in zip(mainloop_row,price_list_source):
        item = {}

        price_s = Selector(text=price_ls)

        segment_list_c = subrow.get("segmentList")

        segment_list = []
        for segment_ls_check in segment_list_c:
            segment_ls_item = {}
            flight_number_chec1 = segment_ls_check.get("flightCode").get("airlineCode")
            flight_number_chec2 =segment_ls_check.get("flightCode").get("flightNumber")
            segment_ls_item['flight_number'] =f"{flight_number_chec1}{flight_number_chec2}"
            segment_ls_item['source'] = segment_ls_check.get("departureAirportCode")

            source_dateTime_check = segment_ls_check.get("departureDateTime")
            dt = datetime.strptime(source_dateTime_check, "%d-%m-%Y %H:%M")
            source_dateTime = dt.strftime("%d-%m-%YT%H:%M:%S")
            segment_ls_item['source_dateTime'] = source_dateTime
            segment_ls_item['destination'] = segment_ls_check.get("arrivalAirportCode")

            destination_dateTime_check = segment_ls_check.get("arrivalDateTime")
            dt = datetime.strptime(destination_dateTime_check, "%d-%m-%Y %H:%M")
            destination_dateTime = dt.strftime("%d-%m-%YT%H:%M:%S")
            segment_ls_item['destination_dateTime'] = destination_dateTime

            segment_ls_item['duration'] = segment_ls_check.get("journeyDurationInMillis")
            segment_list.append(segment_ls_item)

        # Departure info (first segment)
        departure_time_list = [seg.get("departureDateTime") for seg in segment_list_c]
        departure_port_list = [seg.get("departureAirportCode") for seg in segment_list_c]

        # Arrival info (last segment)
        arrival_time_list = [seg.get("arrivalDateTime") for seg in segment_list_c]
        arrival_port_list = [seg.get("arrivalAirportCode") for seg in segment_list_c]

        flight_number_list = []
        for segment in segment_list_c:
            flight_code = segment.get("flightCode", {})
            airlineCode = flight_code.get("airlineCode")
            flightNumber = flight_code.get("flightNumber")
            flight_number_list.append(f"{airlineCode}{flightNumber}")

        if departure_time_list and departure_port_list:
            departure_time_list_0 = departure_time_list[0]
            departure_port_list_0 = departure_port_list[0]

        if arrival_time_list and arrival_port_list:
            arrival_time_list__1 = arrival_time_list[-1]
            arrival_port_list__1 = arrival_port_list[-1]

        #time duration
        time_duration_check = subrow.get("journeyDuration")
        time_duration = convert_minutes(time_duration_check)

        # aircraft type
        city_pair = f"{departure_port_list[0]} {arrival_port_list[-1]}"

        #route
        route_list_check1 = [seg.get("departureAirportCode") for seg in segment_list_c]
        route_list_check2 = [seg.get("arrivalAirportCode") for seg in segment_list_c]
        route_list_set = set(route_list_check1 + route_list_check2)
        route_list_unique = list(route_list_set)

        #Flight section .....
        Flight_price_check = price_s.xpath('//*[contains(text(),"Flight price")]//following-sibling::span//text()').getall()
        Base_fare_check = price_s.xpath('//*[contains(text(),"Base fare")]//following-sibling::span//text()').getall()
        Fuel_surcharge_check = price_s.xpath('//*[contains(text(),"Fuel surcharge")]//following-sibling::span//text()').getall()
        Taxes_and_fees_check = price_s.xpath('//*[contains(text(),"Taxes and fees")]//following-sibling::span//text()').getall()
        Currency = price_s.xpath('//*[contains(@class,"av__style_currency")]/span/text()').get()
        fare_type = price_s.xpath('///span[contains(@class,"av__style_bull_")]/following-sibling::span/text()').get()

        departure_dt = datetime.strptime(departure_time_list[0], "%d-%m-%Y %H:%M")
        arrival_dt = datetime.strptime(arrival_time_list[-1], "%d-%m-%Y %H:%M")

        time_diff = arrival_dt - departure_dt
        days_diff = time_diff.days

        item['Url'] = 'https://www.turkishairlines.com/'
        item['Supplier'] = "Turkish Airlines"
        item['Date Departure'] = departure_dt.strftime("%Y-%m-%d")
        item['Time Departure'] = departure_dt.strftime("%H:%M:%S")
        item['Date Arrival'] = arrival_dt.strftime("%Y-%m-%d")
        item['Time Arrival'] = arrival_dt.strftime("%H:%M:%S")
        item['Dep City'] = Dep_City
        item['Dep Country'] = Dep_Country
        item['Destination  (Main)'] = Destination_Main
        item['Destination (Ticket)'] = Destination_Ticket
        item['Country (Main)'] = Country_Main
        item['Country (Ticket)'] = Country_Ticket
        item['City Pair'] = city_pair
        item['Flight_Number'] = "/".join(flight_number_list)
        item['Route'] = "/".join(route_list_unique)
        item['Servicelevel'] = "Business".upper()
        item['Travel Days Ticket'] = days_diff
        item['FareBasis'] = 'N/A'
        item['FareType'] = fare_type.strip() if fare_type else "N/A"
        item['Type Ticket'] = "One Way".upper()
        item['#Legs'] = len(segment_list)
        item['Class Of Travel'] = 'N/A'
        item['Basefare Ex Tax'] = ("".join(Base_fare_check)).replace("EUR","") if Base_fare_check else 0.00
        item['Amount Airport Tax'] = ("".join(Fuel_surcharge_check)).replace("EUR","") if Fuel_surcharge_check else 0.00
        item['Airline CC Charge'] = ("".join(Taxes_and_fees_check)).replace("EUR","") if Taxes_and_fees_check else 0.00
        item['Amount VAT'] = 0.00
        item['Spend'] = ("".join(Flight_price_check)).replace("EUR","") if Flight_price_check else 0.00
        item['Currency'] = Currency
        item["Scrap_Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # # Create a new MongoDB client for this thread
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection_op = db[COLLECTION_OUTPUT]

        # TODO:: Insert the item
        try:
            collection_op.insert_one(item)
            print("Item inserted successfully!")
        except Exception as e:
            print(f"Error: {e}")

        # client.close

def main_fun():
    input_list = [
        ('AMS', 'SIN', '2025-09-11', 'AMSTERDAM', 'NETHERLANDS', 'SINGAPORE', 'SINGAPORE', 'Singapore', 'SINGAPORE'),
        ('AMS', 'MNL', '2025-09-17','AMSTERDAM','NETHERLANDS','MANILA','MANILA','Philippines','PHILIPPINES'),
    ]
    results_list = []
    for input_ls in input_list:
        source = input_ls[0]
        destination = input_ls[1]
        travel_date = input_ls[2]
        Dep_City = input_ls[3]
        Dep_Country = input_ls[4]
        Destination_Main = input_ls[5]
        Destination_Ticket = input_ls[6]
        Country_Main = input_ls[7]
        Country_Ticket = input_ls[8]

        # st_time = time.time()

        main(source,destination,travel_date,Dep_City,Dep_Country,Destination_Main,Destination_Ticket,Country_Main,Country_Ticket)
    print("Task Completed.....")
    # # print(results_list)
    # df = pd.DataFrame(results_list)
    #
    # now = datetime.now()
    # formatted = now.strftime("%Y%m%d_%H%M%S")
    #
    # # Export to Excel
    # output_path = fr"D:/Danesh/turkishairlines_US_feasibility/save_files/Turkishairline_sampledata_{formatted}.xlsx"
    # df.to_excel(output_path, index=False)
    #
    # print(time.time()- st_time)
    # print(f"Excel file saved to {output_path}")
    # # print("Running counter no. :",counter)

# if __name__ == '__main__':
#     main_fun()
