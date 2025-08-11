import json
import pandas as pd
from datetime import datetime
from main import drission_automation

results_list = []
def convert_minutes(milliseconds):
    seconds = milliseconds // 1000

    # Get hours and minutes
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if hours and minutes:
        return f"{hours}h {minutes}m"
    elif hours:
        return f"{hours}h"
    else:
        return f"{minutes}m"

def main():

    # drission_automation()

    mainpage_path = r"D:\Sharma Danesh\Feasiblility Task\turkishairlines_US_feasibility\demo.json"
    main_content = open(mainpage_path, "r", encoding="utf-8").read()
    json_take = json.loads(main_content)
    mainloop_row = json_take.get("data").get("originDestinationInformationList")[0].get("originDestinationOptionList")

    for subrow in mainloop_row:
        item = {}
        # segment_list = subrow.get("segmentList", [])
        segment_list_c = subrow.get("segmentList")


        #[{"flight_id": "SEG-QR274-AMSDOH-2025-08-15-1615", "flight_number": "QR274", "source": "AMS", "source_dateTime": "2025-08-15T16:15:00", "destination": "DOH", "destination_dateTime": "2025-08-15T23:35:00", "duration": 22800}]
        #segment
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

        #flight_number
        flight_number_list = []
        for segment in segment_list_c:
            flight_code = segment.get("flightCode", {})
            airlineCode = flight_code.get("airlineCode")
            flightNumber = flight_code.get("flightNumber")
            flight_number_list.append(f"{airlineCode}{flightNumber}")


        if departure_time_list and departure_port_list:
            print(departure_time_list[0])
            print(departure_port_list[0])

        if arrival_time_list and arrival_port_list:
            print(arrival_time_list[-1])
            print(arrival_port_list[-1])


        #time duration
        time_duration_check = subrow.get("journeyDuration")
        time_duration = convert_minutes(time_duration_check)
        print(time_duration)

        #Servicelevel
        Servicelevel = subrow.get("fareCategory").get("BUSINESS").get("cabinClass")

        # aircraft type
        city_pair = f"{departure_port_list[0]} {arrival_port_list[-1]}"

        #route
        route_list_check1 = [seg.get("departureAirportCode") for seg in segment_list_c]
        route_list_check2 = [seg.get("arrivalAirportCode") for seg in segment_list_c]
        route_list_set = set(route_list_check1 + route_list_check2)
        route_list_unique = list(route_list_set)
        print(route_list_unique)

        #price
        price = subrow.get("startingPrice").get("amount")
        price_list = []
        price_item = {
            "available_seats": "N/A",
            "price": price,
            "currency": "EUR",
            "base_fare": "N/A",
            "type": "N/A",
        }
        price_list.append(price_item)


        item['url'] = 'https://www.turkishairlines.com/'
        item['supplier'] = "turkishairlines"
        item['route'] = "/".join(route_list_unique)
        item['city_pair'] = city_pair
        item['source'] = departure_port_list[0]
        item['destination'] = arrival_port_list[-1]

        dt = datetime.strptime(arrival_time_list[-1], "%d-%m-%Y %H:%M")
        arrival_time = dt.strftime("%d-%m-%YT%H:%M:%S")
        item['arrival_time'] = arrival_time

        dt = datetime.strptime(departure_time_list[0], "%d-%m-%Y %H:%M")
        departure_time = dt.strftime("%d-%m-%YT%H:%M:%S")
        item['departure_time'] = departure_time

        item["journey_time"] = time_duration
        item['class'] = Servicelevel
        item['flight_type'] = "One Way".upper()
        item['total_stops'] = len(segment_list)
        item['segments'] = segment_list
        item['fares'] = price_list
        item['adults'] = 1

        # now = datetime.now()
        # item['timestamp'] = crawl_time = now.strftime('%d-%m-%Y')
        results_list.append(item)

if __name__ == '__main__':
    main()


print(results_list)
df = pd.DataFrame(results_list)

# Export to Excel
output_path = "Turkishairline_sampledata_11082025.xlsx"
df.to_excel(output_path, index=False)

print(f"Excel file saved to {output_path}")