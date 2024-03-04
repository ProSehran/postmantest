import requests
import pandas as pd
import time
import ipaddress
from datetime import datetime, timezone
from github import Github
import base64
import io

def is_valid_ip(ip_address):
    try:
        ip_obj = ipaddress.IPv4Address(ip_address)
        return True
    except ipaddress.AddressValueError:
        return False

def check_ip_virustotal(api_key, ip_address):
    url = f'https://www.virustotal.com/api/v3/ip_addresses/{ip_address}'
    headers = {
        "accept": "application/json",
        "x-apikey": api_key
    }
    
    try:
        global response
        global last_analysis_stats
        response = requests.get(url, headers=headers)
        response_data = response.json()
        
        last_analysis_stats = response_data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        mal = last_analysis_stats.get("malicious", 0)
        sus = last_analysis_stats.get("suspicious", 0)
        
        global link
        global country_fullname
        global whois_date
        global whois_date_utc
        global last_modification_date
        global last_modification_date_utc
        global as_owner

        link = f"https://www.virustotal.com/gui/ip-address/{ip_address}/detection"
        country = response_data.get("data", {}).get("attributes", {}).get("country")   
        whois_date_utc = response_data.get("data", {}).get("attributes", {}).get("whois_date")      
        # whois_date_utc = response_data["data"]["attributes"]["whois_date"]
        
        last_modification_date_utc = response_data["data"]["attributes"]["last_modification_date"]
        
        as_owner = response_data.get("data", {}).get("attributes", {}).get("as_owner")
        
        country_fullname = get_country_name(country)

        # Check if whois_date_utc is not None before converting
        if whois_date_utc is not None:
            whois_date = datetime.fromtimestamp(whois_date_utc, tz=timezone.utc)
        else:
            whois_date = None
        # whois_date = datetime.fromtimestamp(whois_date_utc, tz=timezone.utc)
        last_modification_date = datetime.fromtimestamp(last_modification_date_utc, tz=timezone.utc)
        

        if response.status_code == 200:
            if mal >= 1:
                return "Malicious"
            elif sus >= 1:
                return "Suspicious"
            else:
                return "Clean"
        elif response.status_code == 400:
            return 400
        else:
            print(f"IP {ip_address} {response.status_code} gave non 200/400 status code... \n")
            return -1  

    except requests.exceptions.RequestException as e:
        print("error in exception \n ",e)
        return 400
    
def checkIP(ip_address, api_key):
    is_malicious = check_ip_virustotal(api_key, ip_address)
    if is_malicious == 400 or is_malicious == -1 or is_malicious == "None":
        print("\n 60 sec sleep, Response code: ",is_malicious,"\n ")
        time.sleep(60)
        return checkIP(ip_address, api_key)
    else:
        return is_malicious


def callAPI(api_key, df, start_index):
    for index in range(start_index-1, len(df)):
        ip_address = df.at[index, 'IP']
        try:
            if is_valid_ip(ip_address):
                is_malicious = checkIP(ip_address, api_key)
                if is_malicious is None:
                    checkIP(ip_address, api_key)    
                else:
                    # Additional code here

                    if whois_date is not None:
                        whois_date_unaware = whois_date.astimezone(timezone.utc).replace(tzinfo=None)
                    else:
                        whois_date_unaware = None
                    
                    last_modification_date_unaware = last_modification_date.astimezone(timezone.utc).replace(tzinfo=None)

                    print(f"\n This {ip_address} is {is_malicious}, country: {country_fullname}, owner: {as_owner} \n ")
                    df.at[index, 'Status'] = is_malicious
                    df.at[index, 'Link'] = link
                    df.at[index, 'last_analysis_stats'] = last_analysis_stats
                    df.at[index, 'Country'] = country_fullname
                    df.at[index, 'whois_date'] = whois_date_unaware
                    df.at[index, 'Last_Modification_Date'] = last_modification_date_unaware
                    df.at[index, 'AS_Owner'] = as_owner
                    
                    df.to_csv('TS_Blocked_IPs.csv', index=False)
            else:
                print(f"{ip_address} is not a valid IP address.")       
                df.at[index, 'Status'] = "Not a valid IP address"
                df.to_csv('TS_Blocked_IPs.csv', index=False)
        except KeyError:
            print(f"KeyError occurred for IP: {ip_address}. Entering 'KeyError' in the 'Status' column.")
            df.at[index, 'Status'] = "KeyError"
            df.to_csv('TS_Blocked_IPs.csv', index=False)

def get_country_name(country_code):
    country_codes = {
    'AF': 'Afghanistan',
    'AL': 'Albania',
    'DZ': 'Algeria',
    'AD': 'Andorra',
    'AO': 'Angola',
    'AG': 'Antigua and Barbuda',
    'AR': 'Argentina',
    'AM': 'Armenia',
    'AU': 'Australia',
    'AT': 'Austria',
    'AZ': 'Azerbaijan',
    'BS': 'Bahamas',
    'BH': 'Bahrain',
    'BD': 'Bangladesh',
    'BB': 'Barbados',
    'BY': 'Belarus',
    'BE': 'Belgium',
    'BZ': 'Belize',
    'BJ': 'Benin',
    'BM': 'Bermuda',
    'BT': 'Bhutan',
    'BO': 'Bolivia',
    'BA': 'Bosnia and Herzegovina',
    'BW': 'Botswana',
    'BR': 'Brazil',
    'BN': 'Brunei',
    'BG': 'Bulgaria',
    'BF': 'Burkina Faso',
    'MM': 'Burma (Myanmar)',
    'BI': 'Burundi',
    'KH': 'Cambodia',
    'CM': 'Cameroon',
    'CA': 'Canada',
    'CV': 'Cape Verde',
    'KY': 'Cayman Islands',
    'CF': 'Central African Republic',
    'TD': 'Chad',
    'CL': 'Chile',
    'CN': 'China',
    'CX': 'Christmas Island',
    'CC': 'Cocos (Keeling) Islands',
    'CO': 'Colombia',
    'KM': 'Comoros',
    'CG': 'Congo',
    'CK': 'Cook Islands',
    'CR': 'Costa Rica',
    'HR': 'Croatia',
    'CU': 'Cuba',
    'CY': 'Cyprus',
    'CZ': 'Czech Republic',
    'CD': 'Democratic Republic of the Congo',
    'DK': 'Denmark',
    'DG': 'Diego Garcia',
    'DJ': 'Djibouti',
    'DM': 'Dominica',
    'DO': 'Dominican Republic',
    'EC': 'Ecuador',
    'EG': 'Egypt',
    'SV': 'El Salvador',
    'GQ': 'Equatorial Guinea',
    'ER': 'Eritrea',
    'EE': 'Estonia',
    'ET': 'Ethiopia',
    'FK': 'Falkland Islands',
    'FO': 'Faroe Islands',
    'FJ': 'Fiji',
    'FI': 'Finland',
    'FR': 'France',
    'GF': 'French Guiana',
    'PF': 'French Polynesia',
    'GA': 'Gabon',
    'GM': 'Gambia',
    'GE': 'Georgia',
    'DE': 'Germany',
    'GH': 'Ghana',
    'GI': 'Gibraltar',
    'GR': 'Greece',
    'GL': 'Greenland',
    'GD': 'Grenada',
    'GP': 'Guadeloupe',
    'GU': 'Guam',
    'GT': 'Guatemala',
    'GN': 'Guinea',
    'GW': 'Guinea-Bissau',
    'GY': 'Guyana',
    'HT': 'Haiti',
    'VA': 'Holy See (Vatican City)',
    'HN': 'Honduras',
    'HK': 'Hong Kong',
    'HU': 'Hungary',
    'IS': 'Iceland',
    'IN': 'India',
    'ID': 'Indonesia',
    'IR': 'Iran',
    'IQ': 'Iraq',
    'IE': 'Ireland',
    'IM': 'Isle of Man',
    'IL': 'Israel',
    'IT': 'Italy',
    'CI': 'Ivory Coast',
    'JM': 'Jamaica',
    'JP': 'Japan',
    'JE': 'Jersey',
    'JO': 'Jordan',
    'KZ': 'Kazakhstan',
    'KE': 'Kenya',
    'KI': 'Kiribati',
    'KW': 'Kuwait',
    'KG': 'Kyrgyzstan',
    'LA': 'Laos',
    'LV': 'Latvia',
    'LB': 'Lebanon',
    'LS': 'Lesotho',
    'LR': 'Liberia',
    'LY': 'Libya',
    'LI': 'Liechtenstein',
    'LT': 'Lithuania',
    'LU': 'Luxembourg',
    'MO': 'Macau',
    'MK': 'Macedonia',
    'MG': 'Madagascar',
    'MW': 'Malawi',
    'MY': 'Malaysia',
    'MV': 'Maldives',
    'ML': 'Mali',
    'MT': 'Malta',
    'MH': 'Marshall Islands',
    'MQ': 'Martinique',
    'MR': 'Mauritania',
    'MU': 'Mauritius',
    'YT': 'Mayotte',
    'MX': 'Mexico',
    'FM': 'Micronesia',
    'MD': 'Moldova',
    'MC': 'Monaco',
    'MN': 'Mongolia',
    'ME': 'Montenegro',
    'MS': 'Montserrat',
    'MA': 'Morocco',
    'MZ': 'Mozambique',
    'NA': 'Namibia',
    'NR': 'Nauru',
    'NP': 'Nepal',
    'NL': 'Netherlands',
    'AN': 'Netherlands Antilles',
    'NC': 'New Caledonia',
    'NZ': 'New Zealand',
    'NI': 'Nicaragua',
    'NE': 'Niger',
    'NG': 'Nigeria',
    'NU': 'Niue',
    'NF': 'Norfolk Island',
    'KP': 'North Korea',
    'MP': 'Northern Mariana Islands',
    'NO': 'Norway',
    'OM': 'Oman',
    'PK': 'Pakistan',
    'PW': 'Palau',
    'PS': 'Palestine',
    'PA': 'Panama',
    'PG': 'Papua New Guinea',
    'PY': 'Paraguay',
    'PE': 'Peru',
    'PH': 'Philippines',
    'PN': 'Pitcairn Islands',
    'PL': 'Poland',
    'PT': 'Portugal',
    'PR': 'Puerto Rico',
    'QA': 'Qatar',
    'CG': 'Republic of the Congo',
    'RE': 'Reunion Island',
    'RO': 'Romania',
    'RU': 'Russia',
    'RW': 'Rwanda',
    'BL': 'Saint Barthelemy',
    'SH': 'Saint Helena',
    'KN': 'Saint Kitts and Nevis',
    'LC': 'Saint Lucia',
    'MF': 'Saint Martin',
    'PM': 'Saint Pierre and Miquelon',
    'VC': 'Saint Vincent and the Grenadines',
    'WS': 'Samoa',
    'SM': 'San Marino',
    'ST': 'Sao Tome and Principe',
    'SA': 'Saudi Arabia',
    'SN': 'Senegal',
    'RS': 'Serbia',
    'SC': 'Seychelles',
    'SL': 'Sierra Leone',
    'SG': 'Singapore',
    'SX': 'Sint Maarten',
    'SK': 'Slovakia',
    'SI': 'Slovenia',
    'SB': 'Solomon Islands',
    'SO': 'Somalia',
    'ZA': 'South Africa',
    'KR': 'South Korea',
    'SS': 'South Sudan',
    'ES': 'Spain',
    'LK': 'Sri Lanka',
    'SD': 'Sudan',
    'SR': 'Suriname',
    'SJ': 'Svalbard',
    'SZ': 'Swaziland',
    'SE': 'Sweden',
    'CH': 'Switzerland',
    'SY': 'Syria',
    'TW': 'Taiwan',
    'TJ': 'Tajikistan',
    'TZ': 'Tanzania',
    'TH': 'Thailand',
    'TL': 'Timor-Leste (East Timor)',
    'TG': 'Togo',
    'TK': 'Tokelau',
    'TO': 'Tonga',
    'TT': 'Trinidad and Tobago',
    'TN': 'Tunisia',
    'TR': 'Turkey',
    'TM': 'Turkmenistan',
    'TC': 'Turks and Caicos Islands',
    'TV': 'Tuvalu',
    'UG': 'Uganda',
    'UA': 'Ukraine',
    'AE': 'United Arab Emirates',
    'GB': 'United Kingdom',
    'US': 'United States',
    'UY': 'Uruguay',
    'VI': 'US Virgin Islands',
    'UZ': 'Uzbekistan',
    'VU': 'Vanuatu',
    'VE': 'Venezuela',
    'VN': 'Vietnam',
    'WF': 'Wallis and Futuna',
    'EH': 'Western Sahara',
    'YE': 'Yemen',
    'ZM': 'Zambia',
    'ZW': 'Zimbabwe'
    }

    if country_code in country_codes:
        return country_codes[country_code]
    else:
        return country_code
               
def main():
    # api_key = '504a439e74d6bd4a5c930e268a7ee61153e828ea998736220c2b7bbd8567d88a'  #IT Vision A/c
    api_key = '04110b16553493a82bcdaa2633dcd6da5224f53fc37d57ecd4c0693ecf3eb058'  #Sehran Rasool A/c
    # api_key = '67cbd99da652226dbdf160af45ebd3b04b3aa5a813ed8353bfbe09e185dd5c07'  #Sehran Jan A/c
    
    df = pd.read_csv('TS_Blocked_IPs.csv')
    df['Status'] = df['Status'].astype('object')
    df['Link'] = df['Link'].astype('object')
    df['last_analysis_stats'] = df['last_analysis_stats'].astype('object')
    df['Country'] = df['Country'].astype('object')
    df['whois_date'] = df['whois_date'].astype('object')
    df['Last_Modification_Date'] = df['Last_Modification_Date'].astype('object')
    df['AS_Owner'] = df['AS_Owner'].astype('object')


    start_index = int(input("\n Enter the starting Sno. from where you want to process IP addresses: "))
    callAPI(api_key, df, start_index)

if __name__ == "__main__":
    main()



#write a program to add 2 numbers in python
