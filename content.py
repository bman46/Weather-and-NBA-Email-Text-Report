#remove unused imports when finished
#get user input for teams and zipcode
from datetime import date, timedelta
import time
#from requests.api import get
from requests.api import get
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import csv
from urllib.request import urlopen



#the 200 means I am allowed to use the information
print(requests.get("https://www.espn.com/nba/scoreboard/_/date/"))

#function within the primary functions getScores() and getSchedule()
def getTeamsPlay(soup,score,teams):
	#finds the html code for the names of teams played and their scores in separate arrays
	playedList = soup.findAll("span",class_="sb-team-short")
	#converts all teams to string format in an array
	pList = [str(i)[str(i).index(">")+1:str(i).rfind("<")] for i in playedList]
	if score:
		timeList = soup.find_all(lambda x:
		(x.name == 'span' or x.name=="th") and
		('time' in x.get('class', []) or 'date-time' in x.get('class', [])) and
		not 'cscore_time' in x['class'] and not 'date_time' in x.get('data-behavior',[]))

		#formats to array of times in string format
		tList =[str(i)[str(i).index(">")+1:str(i).rfind("<")].upper() for i in timeList]
		pListFinal = []
		for a in range(1,len(pList),2):
			if (pList[a-1] in teams or pList[a] in teams) and tList[int(a/2)]!="POSTPONED":
				pListFinal.append(pList[a-1])
				pListFinal.append(pList[a])
	
	else:
		#picks user's teams that played and the opposing team that day
		pListFinal = []
		for a in range(1,len(pList),2):
			if pList[a-1] in teams or pList[a] in teams:
				pListFinal.append(pList[a-1])
				pListFinal.append(pList[a])
	#creates an array with two arrays, with one for all teams playing/played and the other for just the ones of interest
	arr=[]
	arr.append(pList)
	arr.append(pListFinal)
	return arr

#check for what happens with postponed games
def getScores(teams):
	#formats date for the link
	yesterday = str(date.today()-timedelta(days = 1)).replace("-","")

	#makes the default Google Chrome
	driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

	#data I want is in <div id="events" class>
	driver.get("https://www.espn.com/nba/scoreboard/_/date/"+yesterday)
	content = driver.page_source
	soup = BeautifulSoup(content,features="html.parser")
	#html code array for score data
	scoreList = soup.findAll("td",class_="total")
	#builds str array of scores
	sList = []
	for i in scoreList:
		tempStr = ""
		#find("n") skips to later index that is before desired data for faster runtime
		for j in range(len(str(i)[str(i).find("n")]),len(str(i))):
			if(str(i)[j].isnumeric()):
				tempStr+=str(i)[j]
		sList.append(tempStr)


	#gets the desired information in same length arrays that match by index
	pListFinalRef = getTeamsPlay(soup,True,teams)
	pListFinal = pListFinalRef[1]
	sListFinal = [sList[pListFinalRef[0].index(b)] for b in pListFinal]
	
	res = "Yesterday's Scores: \n"
	for c in range(1,len(pListFinal),2):
		if int(sListFinal[c-1])>int(sListFinal[c]):
			res += pListFinal[c-1]+" beat " + pListFinal[c] +' '+ sListFinal[c-1] + "-" + sListFinal[c] +"\n\n"
		elif int(sListFinal[c-1])<int(sListFinal[c]):
			res += pListFinal[c] + " beat " + pListFinal[c-1] +' '+ sListFinal[c] + "-" + sListFinal[c-1] +"\n\n"
	res+="*If you see that a game that you expected is not shown, then that game has been postponed.\n\n\n\n\n"
	return res

#print(getScores(["76ers","Bulls","Trail Blazers","Raptors","Bucks","Nets","Suns"]))

def getSchedule(teams):
	driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
	#automatically goes to today's slate of NBA games
	today = str(date.today()).replace("-","")
	driver.get("https://www.espn.com/nba/scoreboard/_/date/"+today)
	content = driver.page_source
	soup = BeautifulSoup(content,features="html.parser")
	
	#the lambda function strictly matches those with class ="time" and if games are postponed it does the same but for the corresponding header
	#credit to Nuno Andre on https://stackoverflow.com/questions/14496860/how-to-beautiful-soup-bs4-match-just-one-and-only-one-css-class#14516768 for the lambda function
	timeList = soup.find_all(lambda x:
	(x.name == 'span' or x.name=="th") and
	('time' in x.get('class', []) or 'date-time' in x.get('class', [])) and
	not 'cscore_time' in x['class'] and not 'date_time' in x.get('data-behavior',[]))

	#formats to array of times in string format
	tList =[str(i)[str(i).index(">")+1:str(i).rfind("<")].upper() for i in timeList]

	#same procedure as when done in getScores() function
	pListFinalRef = getTeamsPlay(soup,False,teams)
	pListFinal = pListFinalRef[1]


	tListFinal = []
	#accounts for the fact that the number teams playing are double the amount of game times for the day
	for a in range(1,len(pListFinalRef[0]),2):
		if pListFinalRef[0][a-1] in teams or pListFinalRef[0][a] in teams:
			tListFinal.append(tList[int(a/2)])
	

	res = "Today's Slate: \n"
	for b in range(1,len(pListFinal),2):
		res+= pListFinal[b-1] + " at " + pListFinal[b] + " " + tListFinal[int(b/2)] + "\n\n"
	return res + "\n\n\n\n\n"

#print(getSchedule(["76ers","Bulls","Trail Blazers","Raptors","Bucks","Nets","Suns"]))

def getHourlyForecast(zipcodes):
	#csv file from Eric Hurst at https://gist.github.com/erichurst/7882666
	file = open("ZIP,LAT,LNG.csv")
	csvreader = csv.reader(file)
	rows = []
	for line in csvreader:
		rows.append(line)
	#removes the first line
	rows = rows[1:]
	file.close()

	coord = [[] for i in zipcodes]
	#checks if csv file is sorted according to zip code and it checks out
	"""for r in range(1,len(rows)):
		if int(rows[r][0])<int(rows[r-1][0]):
			print("f")"""
	
	for z in range(len(zipcodes)):
		left = 0
		middle = int(len(rows)/2)
		right = len(rows)
		while(coord[z]==[]):
			if int(zipcodes[z])==int(rows[middle][0]):
				coord[z].append(rows[middle][1].strip())
				coord[z].append(rows[middle][2].strip())
				break
			elif left==right:
				coord[z].append(rows[middle][1].strip())
				coord[z].append(rows[middle][2].strip())
				break
			elif int(zipcodes[z])<int(rows[middle][0]):
				right = middle
				middle = int((left+right)/2)
			else:
				left = middle
				middle =int((left+right)/2)
	#read as an online json file
	#since the api code is private I have a filler var for it
	apiCodeFiller = ""
	#PUT IN API CODE TO TEST
	res=""
	for c in coord:
		response = requests.get("https://api.openweathermap.org/data/2.5/onecall?lat=" + c[0] + "&lon=" + c[1] + "&units=imperial&exclude=minutely,daily&appid="+""+apiCodeFiller)
		data = response.json()
		sunrise = time.strftime("%H:%M", time.localtime(int(data["current"]["sunrise"])))
		sunset = time.strftime("%H:%M", time.localtime(int(data["current"]["sunset"])))
		currentTemp = int(data["current"]["temp"])
		currentFeel = int(data["current"]["feels_like"])
		currentUVI = data["current"]["uvi"]
		currentDesc = data["current"]["weather"][0]["description"]
		currentWindSp = data["current"]["wind_speed"]
		#formats string evenly
		res += "Weather for zipcode " + zipcodes[coord.index(c)] +": \n\nSunrise & Sunset:\nSunrise: " + sunrise + "\nSunset: " +sunset + "\n\n"+"Current conditions: \nCurrent Temperature: " + str(currentTemp) + " degrees Fahrenheit" + "\nFeels like: " +str(currentFeel) +" degrees Fahrenheit\nCurrent condition: " + currentDesc + "\nUV index: " + str(currentUVI) + "\nWind Speed: " + str(currentWindSp) + " mph" + "\n\n" 
		#program starts running at  8:05 am and gives the current forecast and hourly forecast for 9 am - 11 pm that day
		#if the user wants it sent at a different time, it will give the current forecast and hourly forecast for the next 14 hours
		#finds temperature, feels like temp, percent chance of percipitation, condition, uvi index, and wind speed for each hour
		tempArr = [str(int(data["hourly"][i]["temp"])) + " degrees Fahrenheit" for i in range(14)]
		feelArr=[str(int(data["hourly"][i]["feels_like"])) + " degrees Fahrenheit" for i in range(14)]
		percPrecArr = [str(100*data["hourly"][i]["pop"]) + "%" for i in range(14)]
		condArr=[data["hourly"][i]["weather"][0]["description"] for i in range(14)]
		uviArr=[data["hourly"][i]["uvi"] for i in range(14)]
		windSpArr = [str(data["hourly"][i]["wind_speed"]) + " mph" for i in range(14)]
		
		for i in range(14):
			res += time.strftime("%H:%M", time.localtime(int(data["hourly"][i]["dt"]))) + '\n'
			res+="Temperature: " + tempArr[i] + "\nFeels like: " + feelArr[i] + "\n"
			res+="Weather: " + condArr[i] + "\nChance of precipitation: " + percPrecArr[i] + "\n"
			res+="UV index: " + str(uviArr[i]) + "\nWind speed: " + windSpArr[i] + "\n\n"
		res += "\n\n\n"
	return res

print(getHourlyForecast(["18976","19122"]))

if __name__ == '__main__':
	pass
