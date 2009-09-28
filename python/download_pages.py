#Standard library
from os import rename, walk
from os.path import splitext

from roman import toRoman

def download():
    # Base url:
    baseurl = 'http://www.netlibrary.com/nlreader/nlReader.dll?BookID=99642&FileName='
    front_start = 1
    front_end = 30
    start_page = 1
    end_page = 487
    
    pages = [baseurl+'Cover.pdf']
    
    for p in range(front_start, front_end+1):
        pages.append(baseurl+'Page_%s.pdf' % toRoman(p).lower())
    
    for p in range(start_page, end_page+1):
        pages.append(baseurl+'Page_%i.pdf' % p)
    
    pages.append(baseurl+'Page_EM1.pdf')
    pages = ['%s\n' % p for p in pages]
    
    f_handle = open('/tmp/page_list.txt', 'wb')
    f_handle.writelines(pages)
    f_handle.close()
    
    cmd = 'wget --wait=30 --random-wait --load-cookies=cookies.txt -i page_list.txt'
    
def get_number(f_name):
    f_name = f_name.split('=')[-1]
    return splitext(f_name)[0].split('_')[1]

def rename_arabic():
    for root, dirs, files in walk('./'):
        for f in files:
            rename(f, 'a_%%03i.pdf' % int(get_number(f)))
            
def rename_roman():
    for root, dirs, files in walk('./'):
        for f in files:
            rename(f, 'r_%s.pdf' % get_number(f))

if __name__ == '__main__':
#    rename_arabic()
    rename_roman()