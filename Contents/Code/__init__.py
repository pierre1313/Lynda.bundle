####################################################################################################

VIDEO_PREFIX = "/video/lynda"

NAME = 'Lynda'

ART  = 'art-default.jpg'
ICON = 'icon-default.png'
SEARCH = 'icon-search.png'
PREFS = 'icon-prefs.png'

filters = {'Subjects':'u','Software':'s','Software Company':'c','Author':'a','Learning Level':'l'}

####################################################################################################

def Start():

    Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, NAME, ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.art = R(ART)
    DirectoryItem.thumb = R(ICON)
    VideoItem.thumb = R(ICON)
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers["User-agent"] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-gb) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16"  

    page_content = HTTP.Request('http://www.lynda.com/allcourses').content
    
    data = page_content[page_content.find("var data = ")+11:]
    data = data[:data.find('};')+1]
    data = data.replace(', ,',',')
    
    Dict['courseCatalog'] = JSON.ObjectFromString(data)

def ValidatePrefs():
    u = Prefs['username']
    p = Prefs['password']
    if (u and p):
      if Login(username=u,password=p) == True:
	    return MessageContainer("Success","You are now logged in, please enjoy the videos")
      else:
        return MessageContainer("Error","You need to provide a valid username and password. Please register at http://www.lynda.com.") 

def Login(username,password):
	valuesLogIn = {"username":username,"password":password,"stayPut":"True"}

	response = HTTP.Request('http://www.lynda.com/user/login/modal',values=valuesLogIn,cacheTime=0).content
    
	if 'rror' in response:
	  return False
	else:
	  return True

def VideoMainMenu():

    dir = MediaContainer(viewGroup="List")

    dir.Append(Function(DirectoryItem(BrowseBy,"Browse by Subject ...",subtitle="Browse the Online Training Library by subject",summary="Browse the Online Training Library by subject"),BrowseCategory = 'Subjects'))
    dir.Append(Function(DirectoryItem(BrowseBy,"Browse by Software ...",subtitle="Browse the Online Training Library by software",summary="Browse the Online Training Library by software"),BrowseCategory = 'Software'))
    dir.Append(Function(DirectoryItem(BrowseBy,"Browse by Vendor ...",subtitle="Browse the Online Training Library by vendor",summary="Browse the Online Training Library by Vendor"),BrowseCategory = 'Software Company'))
    dir.Append(Function(DirectoryItem(BrowseBy,"Browse by Author ...",subtitle="Browse the Online Training Library by author",summary="Browse the Online Training Library by author"),BrowseCategory = 'Author'))
    dir.Append(Function(DirectoryItem(BrowseBy,"Browse by Learning Level ...",subtitle="Browse the Online Training Library by learning level",summary="Browse the Online Training Library by learning level"),BrowseCategory = 'Learning Level'))

    dir.Append(Function(InputDirectoryItem(SearchResults,"Search ...","Search  the Online Training Library",summary="Search  the Online Training Library",thumb=R(SEARCH))))
    dir.Append(PrefsItem(title="Preferences",subtile="",summary="Plug-in preferences",thumb=R(PREFS)))
  
    u = Prefs['username']
    p = Prefs['password']
    auto = Prefs['autologin']
    if (u and p and auto):
      Login(username=u,password=p)
    return dir
    
def BrowseBy(sender, BrowseCategory):
    dir = MediaContainer(viewGroup="List")
    for entry in Dict['courseCatalog']['sections'][BrowseCategory]:
      name = Dict['courseCatalog']['sections'][BrowseCategory][str(entry)]['name']
      if name != '':
        sortindex = Dict['courseCatalog']['sections'][BrowseCategory][str(entry)]['sort']
        dir.Append(Function(DirectoryItem(CourseList,name,subtitle = sortindex),filterKey=filters[BrowseCategory],filterVal = entry))
        dir.Sort('subtitle')
    return dir

def CourseList(sender,filterKey='', filterVal=0, PageNum = 0, pagesEnabled = False, listType= 'lpk3=true'):
    dir = MediaContainer(viewGroup="List")
    for datadict in Dict['courseCatalog']['courses']:
      for key, value in datadict.items():
        try:
          for val in value:
            if key == filterKey and val == int(filterVal) :
              dir.Append(Function(DirectoryItem(CourseDetails,datadict["title"]),courseid = datadict["cid"]))
        except:
          if key == filterKey and value == int(filterVal) :
              dir.Append(Function(DirectoryItem(CourseDetails,datadict["title"]),courseid = datadict["cid"]))
            
    return dir

def CourseDetails(sender, courseid = 0):

    dir = MediaContainer(viewGroup="List")
    html = HTTP.Request('http://www.lynda.com/ajax/CourseDetails.aspx?fn=1&cid=%s&aid=98&cc=&_=1301643565834&{} '%courseid,cacheTime=0).content.replace('</table>','</table></div>').replace("<div  class='chapterDiv' >",' <div class="MychapterDiv"><div  class="chapterDiv" >')
    for entry in HTML.ElementFromString(html).xpath('//div[@class="MychapterDiv"]'):
      Log(HTML.StringFromElement(entry))
      chapterTitle = entry.xpath('//a[@class="a"]')[0].text.strip()
      for course in entry.xpath('table//a'):
        link = course.get('onclick')
        courseTitle = chapterTitle + ' - ' + course.text
        if 'lpk4' in link:
          chapterid = link[link.find('lpk4=')+5:link.find("',")]
          Log(chapterid)
          dir.Append(Function(VideoItem(PlayVideo,courseTitle),chapterid = chapterid))
        else:
          courseTitle = '$$$ - ' + courseTitle
          dir.Append(Function(DirectoryItem(PopupMessage,courseTitle)))

    return dir

def PlayVideo(sender, chapterid):
     return Redirect(XML.ElementFromURL('http://www.lynda.com/home/GetPlayerXML.aspx?lpk4=%s' % chapterid).xpath('//flv')[0].text)

def PopupMessage(sender):
    return MessageContainer(
        "This video requieres a subscription",
        "Please log in. If you do not have a username and password, please register at http://www.lynda.com"
    )

def SearchResults(sender,query=None):

    html = HTTP.Request('http://www.lynda.com/ajax/search.aspx?q=%s&page=1&s=relevance&sa=true&f=producttypeid:4' % query).content
    Content = JSON.ObjectFromString(html)
    if (Content['results']['count']==0):
      return MessageContainer("No Result","Please try again")

    dir = MediaContainer(viewGroup="List")
    for entry in Content['results']['items']:
      courseTitle = entry['courseName']
      chapterid = entry['id']
      if entry['free'] == False:
        courseTitle = '$$$ - ' + courseTitle
        dir.Append(Function(DirectoryItem(PopupMessage,courseTitle)))
      else:
        dir.Append(Function(VideoItem(PlayVideo,courseTitle),chapterid = chapterid))
    
    return dir
