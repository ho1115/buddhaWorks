import googlemaps
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# required install:
# pip install googlemaps (有要爬地區的經緯度才要用)
# pip install pandas (這個應該預設都有裝)
# pip install selenium

# ref: https://github.com/MightyKyloRen/GoogleMapsScrapping/blob/main/main.py 自動scroll的code參考來源

# 全台縣市的經緯度定位，可用getLatLng(place)擴充
Taiwan = {'臺北市': {'lat': 25.0329636, 'lng': 121.5654268}, 
          '新北市': {'lat': 25.0329694, 'lng': 121.5654177}, 
          '桃園市': {'lat': 24.9917033, 'lng': 121.2989587}, 
          '臺中市': {'lat': 24.1477358, 'lng': 120.6736482}, 
          '台南市': {'lat': 22.9997281, 'lng': 120.2270277}, 
          '高雄市': {'lat': 22.6272784, 'lng': 120.3014353}, 
          '新竹縣': {'lat': 24.8387226, 'lng': 121.0177246}, 
          '苗栗縣': {'lat': 24.560159, 'lng': 120.8214265}, 
          '彰化縣': {'lat': 24.0517963, 'lng': 120.5161352}, 
          '南投縣': {'lat': 23.9609981, 'lng': 120.9718638}, 
          '雲林縣': {'lat': 23.7092033, 'lng': 120.4313373}, 
          '嘉義縣': {'lat': 23.4518428, 'lng': 120.2554615}, 
          '屏東縣': {'lat': 22.5519759, 'lng': 120.5487597}, 
          '宜蘭縣': {'lat': 24.7021073, 'lng': 121.7377502}, 
          '花蓮縣': {'lat': 23.9871589, 'lng': 121.6015714}, 
          '台東縣': {'lat': 22.7972447, 'lng': 121.0713702}, 
          '澎湖縣': {'lat': 23.583333, 'lng': 119.583333}, 
          '金門縣': {'lat': 24.34877912595629, 'lng': 118.3285644254523}, 
          '連江縣': {'lat': 26.1505556, 'lng': 119.9288889}, 
          '基隆市': {'lat': 25.1276033, 'lng': 121.7391833}, 
          '新竹市': {'lat': 24.8138287, 'lng': 120.9674798}, 
          '嘉義市': {'lat': 23.4800751, 'lng': 120.4491113}
        }

def getLatLng(place) : # 尋找特定地點的經緯度

    map = googlemaps.Client(key = "申請到的google map api金鑰") # 要付錢，不過每個月有200美金免費額度，大概是28000次response
    geo = map.geocode(place) # 使用的Api名稱: geocoding API

    return(place, geo[0]['geometry']['location']) # example: ('臺北市', {'lat': 25.0329636, 'lng': 121.5654268})

def getStoresInfo(keyword, places, excelPath) : # keyword = 搜索關鍵字, places = 經緯度dict，格式可參照上面的Taiwan, excelPath = excel儲存路徑(含檔名)

    searchedResult = { # 記錄所有爬到的店家資訊，以利輸出成EXCEL
        "店名" : [],
        "分類" : [],
        "地址" : [],
        "網址" : []
    }

    driver = webdriver.Chrome(service = Service(), options = webdriver.ChromeOptions())
    action = ActionChains(driver)

    for key, info in places.items(): # 一一查找所有places dict中的地點
        print("正在搜尋{}的所有{}資訊".format(key, keyword))

        driver.get("https://www.google.com/maps/search/" + keyword + "/@" + str(info['lat']) + "," + str(info['lng']) +",11z/") # 11z是google map的視角高度，數字越小範圍越大
        time.sleep(4)# 等候4秒進行載入
        stores = ""
        storeLen = -1
        indexed = 0
        stores = driver.find_elements(By.CLASS_NAME,"hfpxzc") # 存放店家資訊的<a>的class皆為hfpxzc
        
        if len(stores) == 0 :
            print('無對應的{}{}搜尋結果'.format(key, keyword))
            continue

        while storeLen != len(stores) : #scroll直到沒有新的店家
            storeLen = len(stores)
            for i in range(indexed, storeLen):
                url = stores[indexed].get_attribute("href")
                if not url in searchedResult["網址"] :   # 若是沒有出現過的店家則記錄網址        
                    searchedResult["網址"].append(url)
                indexed += 1
            ori = ScrollOrigin.from_element(stores[storeLen - 1])
            action.scroll_from_origin(ori, 0, 1000).perform()
            time.sleep(2) # 滾動搜索結果並等候2秒
            print("still scrolling, please wait...")
            stores = driver.find_elements(By.CLASS_NAME,"hfpxzc")
        print('已拉至{}{}搜尋結果的頁底'.format(key, keyword))

    print("開始萃取共{}間店家詳細資訊".format(len(searchedResult["網址"]))) # 此為selenium限制，必須先把所有網址記錄起來才能開始改變url
    for i in range(len(searchedResult["網址"])):
        if i % 100 == 0 :
            print("已萃取{}份店家資訊".format(i))
        driver.get(searchedResult["網址"][i])
        time.sleep(1)
        
        try :
            storeName = driver.find_element(By.CLASS_NAME, "DUwDvf.lfPIob").text
        except :
            storeName = "查無店名"
        try :
            sort = driver.find_element(By.CLASS_NAME, "DkEaL").text 
        except :
            sort = "查無分類"
        try :
            addr = driver.find_element(By.CLASS_NAME, "Io6YTe.fontBodyMedium.kR99db").text
        except :
            addr = "查無地址"
        searchedResult["店名"].append(storeName)
        searchedResult["分類"].append(sort)
        searchedResult["地址"].append(addr)
    driver.quit() # 關閉自動網頁

    newExcel = pd.DataFrame(searchedResult)
    newExcel.to_excel(excelPath + '.xlsx', index = False) # 寫入excel
    


getStoresInfo("佛教文物", Taiwan, "./123")