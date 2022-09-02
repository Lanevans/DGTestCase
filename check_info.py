import os
import xml.etree.ElementTree as ET
import json
import ctypes, sys
from datetime import datetime
import getopt

#Config
root_path = os.getcwd()
FIT_path = os.path.join(root_path,'Tools/GfxFwFIT/Windows32/')
Info_path = os.path.join(root_path,'Tools/GfxFwInfo/Windows64/')
Script_path = os.path.join(root_path,'Script/')



argv = sys.argv[1:]

opts, args = getopt.getopt(argv,"t:")


# Get the value after -t
# ex: python main.py -t 10
# opts = [('-t','10')] , opt = '-t'; arg = '10'
for opt, arg in opts:
    if opt in ['-t']:
        time = arg

# Log path (where you store the log file), e.g.Log/10/
Log_path = os.path.join(root_path,'Log/{}'.format(time))


def Retrieve_Info():

    os.chdir(Info_path)
    

    # check info lists <-- the only information we want to retrieve
    check_list = ['GfxFW Status Register1',
                'GfxFW Status Register5',
                'Current GfxFW State',
                'GSC Boot Type',
                'Device ID',
                'GFX FW Version',
                'GFI Driver Version',
                'OPROM Version',
                'GSC FW Version',
                'PUnit FW Version',
                'GT Subsystem Vendor ID',
                'GT Subsystem Device ID',
                'LMEMBAR',
                'Default Boot Profile Selected',
                'Number of board profiles created']

    # Read Info File
    with open('info.txt') as f:
        data = f.readlines()

    # Store data in json type
    info = {}

    for line in data:        
        try:
            lines = line.replace('\n','').split('     ')
            while('' in lines):
                lines.remove('')
            
            if len(lines) == 2:
                key = lines[0];value = lines[1]
                for check_name in check_list: 
                    if check_name.replace(' ','') == key.replace(' ',''):
                        value = value.replace(' ','')
                        info[check_name] = value
        except:
            continue
    
    with open('data.json', 'w') as fp:
        json.dump(info, fp)
    print('Create Info Check List Success')

    

def Check_Info_with_XML():
    

    os.chdir(Info_path)
    #   Load Info File
    with open('data.json', 'r') as fp:
        info_data = json.load(fp)
    
    
    #   Ex : DG02_2.2270 
    Gfx_version = info_data['GFX FW Version']

    os.chdir(FIT_path)
    #   Search XML File with Gfx_version
    print('Search Xml File with Gfx Version: \n')


    #   Using Gfx_version name to find xml file
    file_ex_name = '.xml'
    for item in os.listdir():
        file_name,file_ext = os.path.splitext(item)
        if Gfx_version in file_name and file_ext == file_ex_name:
            xml_file = item


    #   Parse xml file with ET module
    tree = ET.parse(xml_file)
    root = tree.getroot()

    #   Find Device Id(Sku Version)
    sku_version = root.attrib['sku'] 
    if sku_version == info_data['Device ID']:
        print('check {:22}'.format('Device ID'),' success')
        
    #   Find GFX FW Version
    Gfx_version = (root.findall('.//GfxFwRegion'))[0].find('ExternalVersion').get('value')
    if Gfx_version == info_data['GFX FW Version']:
        print('check {:22}'.format('GFX FW Version'),' success')

    # Find the Boot Profile Info
    profiles = root.findall('.//BoardProfilesPolicies')

    #   Check Default Boot Profile Number
    #   Ex :  profile_value = Profile 0
    profile_value = profiles[0].find('BoardBootProfile').get('value')

    #   Change profile_value to interger
    #   profile_value = Profile 0 --> 0
    profile_value = int(profile_value.replace('Profile ',''))


    # Find the numbers of all profile
    SpdProfiles = profiles[0].findall('SpdProfiles')[0]
    print('Number of board profiles created = 0x0{}'.format(len(SpdProfiles)))

    # Profile <-- The Default Boot Profile Info
    Profile = SpdProfiles[profile_value]
    print('Default Boot Profile = ',info_data['Default Boot Profile Selected'])


    #   table contains key:value pairs
    #   beacause there are some keyname in info different from xml
    #   so we create a lookup table (key-value pair), e.g. key = Lmembar; value =  LMEMBAR.
    table = {'Lmembar':'LMEMBAR','GtSsDevIdConfig':'GT Subsystem Device ID','GtSsVenIdConfig':'GT Subsystem Vendor ID'}

    #   check the value between info and xml
    for child in Profile:
        for key in table:

            # if the check name is equal to tag, then check the value
            # e.g.  <GtSsVenIdConfig value="0x1043" />
            # e.g. tag = GtSsVenIdConfig ; attrib['value'] = 0x1043
            if key == child.tag:
                xml_value = child.attrib['value']
                table_value = table[key]
                info_value = info_data[table_value]

                # if the value betwenn xml and info is equal, echo 'success'
                if xml_value.upper() == info_value.upper():
                    print('check {:22}'.format(table_value),' success')
                else:
                    print('-'*20)
                    print('check {:22}'.format(table_value),' error!')
                    print('xml file value =',xml_value)
                    print('info value =',info_value)
                    print('-'*20)


def Check_Info_with_PowerShell():
    os.chdir(Script_path)
    command = 'powershell.exe -file "check_GFI&AUX.ps1"'
    os.system(command)

    # Intel(R) Graphics System Controller Firmware Interface Driver Version
    with open('GFI_Driver_Ver.txt','r') as f:
        GFI_data = f.readlines()

    for line in GFI_data:
        if '.' in line:
            GFI_value = line.replace('\n','')
            GFI_value = GFI_value.replace(' ','')
            GFI_value = GFI_value.replace(line[0],'')

    # Intel(R) Graphics System Controller Auxiliary Firmware Interface Driver Version
    with open('AUX_Driver_Ver.txt','r') as f:
        AUX_data = f.readlines()

    for line in AUX_data:
        if '.' in line:
            AUX_value = line.replace('\n','')
            AUX_value = AUX_value.replace(' ','')
            AUX_value = AUX_value.replace(line[0],'')

    os.chdir(Info_path)

    check_name = 'GFI Driver Version'
    with open('data.json', 'r') as fp:
        info_data = json.load(fp)

    # Append AUX Driver Version Value in data.json
    info_data['AUX Driver Version'] = AUX_value

    GFI_Driver_Version = info_data['GFI Driver Version']

    if GFI_Driver_Version == GFI_value:
        print('check {:22}'.format(check_name), ' success')
    else:
        print('check {:22}'.format(check_name),' error!')

    with open('data.json', 'w') as fp:
        json.dump(info_data, fp)

    print('{:16} = '.format('AUX Driver Version'),AUX_value)



def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if is_admin():
    
    time = datetime.now()
    time = time.strftime("%Y-%m-%d %H:%M:%S")
    
    print('Start Checking Info ........')
    print('Check Info Start Time = ',time)

    print('\nStep 1 : Create Info File with GfxFwInfo.exe')
    os.chdir(Info_path)
    commands = 'GfxFwInfoWin64.exe -VERBOSE info.txt'
    os.system(commands)
    print('Create Info File Success')

    Retrieve_Info()
    print('Retrieve Info Success')
    print('='*20)

    print('Step 2 : Check Info Along with XML File\n')
    Check_Info_with_XML()
    Check_Info_with_PowerShell()


    time = datetime.now()
    time = time.strftime("%Y-%m-%d %H:%M:%S")
    
    print('Check Info End Time = ',time)
    print('='*20,'\n')

else:
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)


