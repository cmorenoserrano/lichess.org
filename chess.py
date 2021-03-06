#!/usr/bin/python3
## ----------------------------------------------------------------------------
## Python Dependencies
import os
from copy import deepcopy
import datetime
import time
import urllib
import urllib.request
from urllib.request import urlopen
import requests
import json, argparse
import ndjson
from fpdf import FPDF
import shutil
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import re

## ----------------------------------------------------------------------------
session = requests.Session()

def getPlayerStats(username):
    baseUrl = "https://api.chess.com/pub/player/" + username + "/stats"

    response = session.get(baseUrl)
    stats = response.json()
    dumps(stats,file_name=username+'/stats.json')
    #print(stats)
    return stats

def getECF(clubcode):
    baseUrl = "https://www.ecfrating.org.uk/v2/new/list_players.php?mode=A&moc=&search=&ECF_code=&club_code="+clubcode+"&assoc_code=&nation=&member_class="

    details = []
    only_td = SoupStrainer("td")
    page = urlopen(baseUrl)
    html = page.read().decode('utf-8')
    soup = BeautifulSoup(html,'html.parser',parse_only=only_td).prettify()
    #print(soup)

    soup = re.sub("<td.*?>","TTT",soup)
    soup = re.sub("</td.*?>","DDD",soup)
    soup = re.sub("<.*?>","",soup)
    soup = soup.strip()
    soup = soup.replace("\n","")    
    #print(soup)
    data = soup.partition("TTT")[2].partition("DDD")[0]
    rest = soup.partition("TTT")[2].partition("DDD")[2]
    details.append(data)
    #print(details)
    while(len(rest) > 0):
        data = rest.partition("TTT")[2].partition("DDD")[0]
        rest = rest.partition("TTT")[2].partition("DDD")[2]
        details.append(data)
    #print(details)
    ecfdata = []
    fields = ["No.","ECF Code","Member No.","ECF","Sex","Nat.","First Name","Last Name","Club","Assoc.","Last Game","OTB Standard","OTB Rapid","Online Standard","Online Rapid","Online Blitz"]
    for j in range(0,int(len(details)/16)):
        aux = {}
        for i in range(0,len(fields)):
            aux.update({fields[i]:details[i+16*j]})
        ecfdata.append(aux)
    #print(ecfdata[195]["Last Name"])
    return ecfdata

def getPlayerDetails(username):
    baseUrl = "https://lichess.org/api/user/" + username
    
    response = session.get(baseUrl)
    details = response.json()
    dumps(details,file_name=username+'/user_details.json')

    #print(stats)
    return details


def getPlayerRatingHistory(username):
    baseUrl = "https://lichess.org/api/user/" + username + "/rating-history"

    response = session.get(baseUrl)
    details = response.json()
    dumps(details,file_name=username+'/rating-history.json')

    #print(stats)
    return details

def getPlayerPerformance(username):
    baseUrl = "https://lichess.org/api/user/" + username + "/perf/"
    perf = ['ultraBullet','bullet','blitz','rapid','classical','correspondence']
    for parameter in perf:    
        response = session.get(baseUrl+parameter)
        #print(response)
        details = response.json()
        dumps(details,file_name=username+'/perf_'+parameter+'.json')
    #print(stats)
    return details


def getUserGames(username):
    #username = "sprocket314"
    baseUrl = "https://lichess.org/api/games/user/" + username + "?opening=true&evals=true&pgnInJson=true&rated=true&since=1609459200000"
    headers = {'Accept': 'application/x-ndjson',}
    response = requests.get(baseUrl, headers=headers)
    #print(response)
    games = response.json(cls=ndjson.Decoder)
    dumps(games,file_name=username+'/games.json')
    return games

def getClubDetails(clubname):
    baseUrl = "https://lichess.org/api/team/" + clubname + "/users"
    members = []
    response = session.get(baseUrl)
    clubDetails = response.json(cls=ndjson.Decoder)
    dumps(clubDetails,file_name=clubname+'/club_details.json')
    #print(clubDetails[0]["id"])
    #print(len(clubDetails))
    for i in range(0,len(clubDetails)):
        members.append(clubDetails[i]["username"])
    #print(members)
    return members

def getMembersDetails(club,members):
    #print(len(members))
    for i in range(0,len(members)):
        #print(members[i])
        if not os.path.exists(club + "/members/"):
            os.mkdir(club + "/members/")
        if not os.path.exists(club + "/members/" + members[i]):
            os.mkdir(club + "/members/" + members[i])
        baseUrl = "https://lichess.org/api/user/" + members[i]
        response = session.get(baseUrl)
        details = response.json()
        #print(details)
        dumps(details,file_name=club + "/members/" + members[i]+'/user_details.json')
        time.sleep(1)
        
    return


def getMembersRating(club,clubcode):
    membersRating = []
    ecf = getECF(clubcode)
    print(ecf)

    return membersRating




def getClubMatches(clubname):
    baseUrl = "https://api.chess.com/pub/club/" + clubname + "/matches"

    response = session.get(baseUrl)
    matches = response.json()
    dumps(matches,file_name=clubname+'/matches.json')
    #print(matches)
    return matches

def getResults(clubname,members,scope_finished,scope_in_progress):
    #print(scope_finished)
    t, graphNo = 0, len(scope_finished)
    if len(scope_finished) != 0:
        printProgressBar(t,graphNo)
    clubUrl = "https://api.chess.com/pub/club/" + clubname
    results = {}
    
    for match in scope_finished:
        t+=1
        if len(scope_finished) != 0:
            printProgressBar(t,graphNo)
        baseUrl = match["@id"]
        response = session.get(baseUrl)
        team_match = response.json()
        if not os.path.exists(clubname+"/club_matches_finished"):
            os.mkdir(clubname+"/club_matches_finished")
        dumps(team_match,file_name=clubname+'/club_matches_finished/'+match["name"]+'.json')
        for team in team_match["teams"]:
            if team_match["teams"][team]["@id"] == clubUrl:
                for player in team_match["teams"][team]["players"]:
                    if "played_as_black" in player:
                        if player["played_as_black"] == "win" and player["username"] in members:
                            members[player["username"]] += 1
                        if player["played_as_black"] == ("insufficient" or "agreed" or "repetition" or "stalemate" or "50move" or "threecheck" or "timevsinsufficient") and player["username"] in members:
                            members[player["username"]] += 0.5
                    if "played_as_white" in player:
                        if player["played_as_white"] == "win" and player["username"] in members:
                            members[player["username"]] += 1
                        if player["played_as_white"] == ("insufficient" or "agreed" or "repetition" or "stalemate" or "50move" or "threecheck" or "timevsinsufficient") and player["username"] in members:
                            members[player["username"]] += 0.5

    #print(scope_in_progress)
    t, graphNo = 0, len(scope_in_progress)
    if len(scope_in_progress) != 0:
        printProgressBar(t,graphNo)
    for match in scope_in_progress:
        t+=1
        if len(scope_in_progress) != 0:
            printProgressBar(t,graphNo)
        baseUrl = match["@id"]
        response = session.get(baseUrl)
        team_match = response.json()
        if not os.path.exists(clubname+"/club_matches_in_progress"):
            os.mkdir(clubname+"/club_matches_in_progress")
        dumps(team_match,file_name=clubname+'/club_matches_in_progress/'+match["name"]+'.json')
        for team in team_match["teams"]:
            if team_match["teams"][team]["@id"] == clubUrl:
                for player in team_match["teams"][team]["players"]:
                    if "played_as_black" in player:
                        if player["played_as_black"] == "win" and player["username"] in members:
                            members[player["username"]] += 1
                        if player["played_as_black"] == ("insufficient" or "agreed" or "repetition" or "stalemate" or "50move" or "threecheck" or "timevsinsufficient") and player["username"] in members:
                            members[player["username"]] += 0.5
                    if "played_as_white" in player:
                        if player["played_as_white"] == "win" and player["username"] in members:
                            members[player["username"]] += 1
                        if player["played_as_white"] == ("insufficient" or "agreed" or "repetition" or "stalemate" or "50move" or "threecheck" or "timevsinsufficient") and player["username"] in members:
                            members[player["username"]] += 0.5

    ranking = []
    for player in members:
        points = [members[player]]
        ranking.append([player] + points)
    ##########################################################################
    ranking.sort(key = lambda ranking : ranking[1], reverse = True)
    ##########################################################################
    #print(ranking)
                            
    results = ranking
    dumps(results,file_name=clubname+'/results.json')
    return results

# Print iterations progress
def printProgressBar (
        iteration, 
        total, 
        prefix = 'Progress:', 
        suffix = 'Complete', 
        decimals = 1, 
        length = 50, 
        fill = '???'):

    time.sleep(0.1)
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()

#---------------------------------

def generateLeagueTable(clubname,results, start_date, end_date,logo):
    t, graphNo = 0, len(results)
    printProgressBar(t,graphNo)
    pdf = PDF()
    pdf.alias_nb_pages()
    #components = final
    header = ['Position','Member','Daily rating','Points']
    data = []
    for i in range(1,len(results)+1):
        t+=1
        printProgressBar(t,graphNo)
        if results[i-1][1] > 0:
            aux = [str(i),results[i-1][0],str(getPlayerStats(results[i-1][0])["chess_daily"]["last"]["rating"]),str(results[i-1][1])]
            data.append(aux)
    #print(data)
    pdf.print_chapter("League Table for "+clubname+"'s Club Daily Matches","",logo)
    pdf.set_font('Times','',12)
    pdf.set_text_color(0,0,0)
    instructions = "Current standings from "+str(start_date)+" to "+str(end_date)
    pdf.multi_cell(0,7,instructions,0)
    pdf.ln(5)
    pdf.set_font('Times','',12)
    pdf.fancy_table(header,data)

    if not data:
        print("\nThere was no data available")
        raise SystemExit
    details = getPlayerDetails(data[0][1])
    #print(details)
    stats = getPlayerStats(data[0][1])

    pdf.print_chapter('Player of the Month',"",logo)
    pdf.set_font('Times','B',24)
    pdf.set_text_color(0,0,0)
    content1 = "This month's Player of the Month was: "+str(data[0][1])
    pdf.multi_cell(0,7,content1,0)
    pdf.ln(5)
    if "avatar" in details:
        pdf.image(details["avatar"], 230, 50, 33)
        #pdf.image(details["avatar"], 230, 50, 33, type='jpeg')
    else:
        pdf.image("defaultLogo.jpeg",230,50,33, type='jpeg')
    pdf.set_font('Times','B',18)
    content2 = str(data[0][1])+" achieved "+str(data[0][3])+" points in Daily Matches representing our club"
    pdf.multi_cell(0,7,content2,0)
    pdf.ln(10)
    content3 = "Getting to know "+details["username"]+ " better:"
    pdf.multi_cell(0,7,content3,0)
    pdf.ln(5)
    if "name" in details:
        content4 = "Name: "+details["name"]
        pdf.multi_cell(0,7,content4,0)
        pdf.ln(5)
    content5 = "Joined on "+ time.strftime('%d-%b-%Y', time.localtime(details["joined"]))
    pdf.multi_cell(0,7,content5,0)
    pdf.ln(5)
    content6 = "Daily rating: "+str(stats["chess_daily"]["last"]["rating"])+" (current), "+str(stats["chess_daily"]["best"]["rating"])+ " (best)"
    pdf.multi_cell(0,7,content6,0)
    pdf.ln(5)
    if "chess960_daily" in stats:
        content7 = "Daily 960 rating: "+str(stats["chess960_daily"]["last"]["rating"])+" (current), "+str(stats["chess960_daily"]["best"]["rating"])+ " (best)"
        pdf.multi_cell(0,7,content7,0)
        pdf.ln(5)
    if "chess_rapid" in stats:
        content8 = "Rapid rating: "+str(stats["chess_rapid"]["last"]["rating"])+" (current), "+str(stats["chess_rapid"]["best"]["rating"])+ " (best)"
        pdf.multi_cell(0,7,content8,0)
        pdf.ln(5)
    if "chess_blitz" in stats:
        content9 = "Blitz rating: "+str(stats["chess_blitz"]["last"]["rating"])+" (current), "+str(stats["chess_blitz"]["best"]["rating"])+ " (best)"
        pdf.multi_cell(0,7,content9,0)
        pdf.ln(5)
    if "chess_bullet" in stats:
        if "best" in stats["chess_bullet"]:
            content10 = "Bullet rating: "+str(stats["chess_bullet"]["last"]["rating"])+" (current), "+str(stats["chess_bullet"]["best"]["rating"])+ " (best)"
        else:
            content10 = "Bullet rating: "+str(stats["chess_bullet"]["last"]["rating"])+" (current)"
        pdf.multi_cell(0,7,content10,0)
        pdf.ln(5)
    if "tactics" in stats:
        content11 = "Tactics rating: "+str(stats["tactics"]["highest"]["rating"])+" (highest)"
        pdf.multi_cell(0,7,content11,0)
        pdf.ln(5)
    if "puzzle_rush" in stats:
        if "best" in stats["puzzle_rush"]:
            content6 = "Puzzle Rush score: "+str(stats["puzzle_rush"]["best"]["score"])+" (record)"
        pdf.multi_cell(0,7,content6,0)
        pdf.ln(5)
    


    pdf.set_font('Times','',12)
    pdf.set_text_color(0,0,0)
    #insert avatar
    #insert ratings
    
    pdf.output(clubname+'/leagueTable.pdf', 'F')
    #print("PDF generated -> leagueTable.pdf")




def getArguments():
    global baseUrl
    parser = argparse.ArgumentParser(description='Chess.com API data handling script')
    parser.add_argument('-u','--username', help='Specific username', required=False)
    parser.add_argument('-ug','--userGames', help='Download all archived games for a specified user', action='store_true', required=False)
    parser.add_argument('-c','--club', help='Specific club', required=False)
    parser.add_argument('-d','--dateRange',help='Specify a date range: dd-mm-yyyy:dd-mm-yyyy',required=False)
    parser.add_argument('-r','--report',help='Generate League table report',action='store_true',required=False)
    
    args = vars(parser.parse_args())
    return args
#-----------------------------------------------------------------------------

#---------------------------------

class PDF(FPDF):
    def header(self,logo):
        # Logo
        self.image(logo, 10, 8, 33)
        #self.image('team_uk_logo.jpeg', 10, 8, 33)
        # Times bold 15
        self.set_font('Times', 'B', 15)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(100, 10, 'League Table', 1, 0, 'C')
        # Line break
        self.ln(20)

        # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Times', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

        #Chapter title
    def chapter_title(self, title):
        # Arial 12
        self.set_font('Times', 'B', 12)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Line break
        self.ln(10)
        # Title
        self.cell(0, 6, '%s' % (title), 0, 1, 'L', 1)
        # Line break
        self.ln(0)

        #Chapter body
    def chapter_body(self, content_dict):
        # Times 12
        self.set_font('Times', '', 12)
        # Output justified text
        for field in content_dict:
            self.cell(0, 5, field+": "+content_dict[field], 1, 1)
        # Line break
        self.ln()

        #Print chapter
    def print_chapter(self, title, content, logo):
        self.add_page('L', format = 'a4', logo = logo)
        self.chapter_title(title)
        self.chapter_body(content)

    def print_list(self,data):
        self.cell()

    def fancy_table(this,header,data):
        #Colors, line width and bold font
        this.set_fill_color(255,0,0)
        this.set_text_color(255)
        this.set_draw_color(128,0,0)
        this.set_line_width(.3)
        this.set_font('Times','B')
        #Header
        w=[]
        column_no = len(header)
        page_width = 277 #magic number for A4 in mm
        column_width = page_width/column_no
        for i in range(0,column_no):
            w.append(column_width)
        for i in range(0,column_no):
            this.cell(w[i],7,header[i],1,0,'C',1)
        this.ln()
        #Color and font restoration
        this.set_fill_color(224,235,255)
        this.set_text_color(0)
        this.set_font('Times')
        #Data
        fill=0
        for row in data:
            for i in range(0,column_no):
                this.cell(w[i],6,row[i],'LR',0,'C',fill)
                #print(row[i])
            this.ln()
            fill=not fill
        this.cell(sum(w),0,'','T')

    def dynamic_table(this,header,data):
        #Colors, line width and bold font
        this.set_fill_color(255,0,0)
        this.set_text_color(255)
        this.set_draw_color(128,0,0)
        this.set_line_width(.3)
        this.set_font('Times','B')
        #Header
        w=[]
        column_no = len(header)
        page_width = 277 #magic number for A4 in mm
        column_width = page_width/column_no
        for i in range(0,column_no):
            w.append(column_width)
        for i in range(0,column_no):
            this.cell(w[i],7,header[i],1,0,'C',1)
        this.ln()
        #Color and font restoration
        this.set_fill_color(224,235,255)
        this.set_text_color(0)
        this.set_font('Times')
        #Data
        fill=0
        for row in data:
            for i in range(0,column_no):
                this.multi_cell(w[i],6,row[i],1,'L',fill)
                fill=not fill
                this.multi_cell(w[i],6,row[i+1],1,'L',fill)
                fill=not fill
                this.ln()
        this.cell(sum(w),0,'','T')
        return

#---------------------------------

def output_pdf(pages, filename):
    pdf = FPDF()
    pdf.set_font('Times','B',12)
    for image in pages:
        pdf.add_page('L')
        pdf.set_xy(0,0)
        pdf.image(image, x = None, y = None, w = 0, h = 0, type = '', link = '')
    pdf.output(filename, 'F')
    return


#---------------------------------


#-----------------------------------------------------------------------------
def main():
    #t, graphNo = 0, 4
    #printProgressBar(t,graphNo)
    username = ""
    club = ""
    clubcode = "7072" #Club code for Guildford Chess Club
    scope_finished = {}
    scope_in_progress = {}
    args = getArguments()


    if args["dateRange"]:
        dateRange = args["dateRange"].split(":",1)
        first = dateRange[0].split("-",2)
        last = dateRange[1].split("-",2)
        start_date = dateRange[0]
        start_epoch = round(datetime.datetime(int(first[2]),int(first[1]),int(first[0])).timestamp())
        end_date = dateRange[1]
        end_epoch = round(datetime.datetime(int(last[2]),int(last[1]),int(last[0])).timestamp())

    #t +=1
    #printProgressBar(t,graphNo)

    
    if args["username"]:
        username = args["username"]
        if not os.path.exists(username):
            os.mkdir(username)
        getPlayerDetails(username)
        getPlayerRatingHistory(username)
        getPlayerPerformance(username)
        getUserGames(username)
#        getPlayerStats(username)

    #t +=1
    #printProgressBar(t,graphNo)

    if args["userGames"]:
        if args["username"]:
            getUserGames(username)

    #t +=1
    #printProgressBar(t,graphNo)

    if args["club"]:
        club = args["club"]
        if not os.path.exists(club):
            os.mkdir(club)
        membersRating = getMembersRating(club,clubcode)
        members = getClubDetails(club)
        getMembersDetails(club,members)
        #clubLogo = getClubLogo(club)
        #members = getClubMembers(club)
        #matches = getClubMatches(club)
        #if args["dateRange"]:
        #    scope_finished = list(filter(lambda match: (match["start_time"] >= start_epoch) and (match["start_time"] <= end_epoch), matches["finished"]))
        #    scope_in_progress = matches["in_progress"]

    #t +=1
    #printProgressBar(t,graphNo)

    if args["report"]:
        if args["club"]:
            if args["dateRange"]:
                t, graphNo = 0, 5
                printProgressBar(t,graphNo)
                members = {}
                clubMembers = getClubMembers(club)
                for member in clubMembers["weekly"]:
                    members.update({member["username"] : 0})
                for member in clubMembers["monthly"]:
                    members.update({member["username"] : 0})
                for member in clubMembers["all_time"]:
                    members.update({member["username"] : 0})
                matches = getClubMatches(club)

                #t +=1
                #printProgressBar(t,graphNo)

                scope_finished = list(filter(lambda match: (match["start_time"] >= start_epoch) and (match["start_time"] <= end_epoch), matches["finished"]))

                #t +=1
                #printProgressBar(t,graphNo)
                
                scope_in_progress = matches["in_progress"]

                #t +=1
                #printProgressBar(t,graphNo)

                results = getResults(club,members,scope_finished,scope_in_progress)

                #t +=1
                #printProgressBar(t,graphNo)
                
                generateLeagueTable(club,results,start_date,end_date,getClubLogo(club))

                #t +=1
                #printProgressBar(t,graphNo)


  

    #####Present League Table by tiers ranked based on points
    #####Additional features like player of the week, most improved player, top ranking by time control, etc.
    


	
#-----------------------------------------------------------------------------
def pp(c):
    print( json.dumps(c, indent=4) )

def dumps(page, pretty = True, file_name = "results.json"):
    try:
        if pretty: page = json.dumps(page, indent=4)
        with open(file_name,"w+") as file:
            file.write(page)
    finally:
        return page

def handle_resp(resp, root=""):
    if resp.status_code != 200: 
        print(resp.text)
        return None
    node = resp.json()
    if root in node: node = node[root]
    if node == None or len(node) == 0: return None
    return node

def get_url(url, root=""):
    resp = iq_session.get(url)
    return handle_resp(resp, root)

def post_url(url, params, root=""):
    resp = iq_session.post(url, json=params)
    return handle_resp(resp, root)

def get_epoch(epoch_ms):
    dt_ = datetime.datetime.fromtimestamp(epoch_ms/1000)
    return dt_.strftime("%Y-%m-%d %H:%M:%S")

def get_applicationId(publicId):
    url = f'{iq_url}/api/v2/applications?publicId={publicId}'
    apps = get_url(url, "applications")
    if apps == None: return None
    return apps[0]['id']

def get_reportId(applicationId, stageId):
    url = f"{iq_url}/api/v2/reports/applications/{applicationId}"
    reports = get_url(url)
    for report in reports:
        if report["stage"] in stageId:
            return report["reportHtmlUrl"].split("/")[-1]

def get_policy_violations(publicId, reportId):
    url = f'{iq_url}/api/v2/applications/{publicId}/reports/{reportId}/policy'
    return get_url(url)

def get_recommendation(component, applicationId, stageId):
    url = f'{iq_url}/api/v2/components/remediation/application/{applicationId}?stageId={stageId}'
    return post_url(url, component)

def get_last_version(component):
    url = f"{iq_url}/api/v2/components/versions"
    return post_url(url, component)
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

if __name__ == "__main__":
    main()

