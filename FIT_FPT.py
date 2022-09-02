import os
import shutil
import xml.etree.ElementTree as ET
import json
from datetime import datetime
import ctypes, sys
import getopt


# Config Data
Origin_Bin_Name = None      
Origin_Bin_Path = None
Origin_Bin_Version = None

Target_Bin_Name = None      # The target bin name equal to the bin file name under "Firmware Image" folder
Target_Bin_Version = None   # ex: bin file name = "Graphics_Firmware_DG02_2.2270_production_B-step.bin", then bin version is "2270"

Update_Xml_Name = None
Update_Xml_File = None

New_Bin_Path = None

# Inital value = MRB
Device_Type = "MRB"

# root_path = current folder path
root_path = os.getcwd()
FIT_path = os.path.join(root_path,'Tools/GfxFwFIT/Windows32/')
FPT_path = os.path.join(root_path,'Tools/GfxFwFPT/Windows64/')
Firmware_Path = os.path.join(root_path,'Firmware Image/')
data ={}

# Let this program run as Administrator
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def Create_XML():

    ######################################################################################################
    ###############     This function will create a xml file from original bin          ##################
    ############     The function can be executed by declare the global variable first     ###############
    ####### Or you can let the function search the original bin file and file name then executed #########
    ######################################################################################################


    # If you want to modify global variable inside the function, you need to declare variable with "global" character in front of variables
    global Origin_Bin_Name,Origin_Bin_Path


    if Origin_Bin_Name == None and Origin_Bin_Path == None:

        print('Search origin bin file: \n')

        # Search the file under the folder with ".bin" as its extension name
        # Then pass the filepath and filename to global variable (Origin_Bin_Path) and (Origin_Bin_Name)
        file_ex_name = '.bin'
        for item in os.listdir():
            file_name,file_ext = os.path.splitext(item)
            if os.path.isfile(item) and file_ext == file_ex_name:
                Origin_Bin_Name = file_name
                Origin_Bin_Path = os.path.join(os.getcwd(),item)
                print("origin file path = ",Origin_Bin_Path)
                print("origin file name = ",Origin_Bin_Name)


    

    # Load origin bin file with FIT Tool and Save XML File
    print('Loading origin bin file with FIT Tool: \n')

    os.chdir(FIT_path)

    # Use original bin to create a xml file and we can modify this xml file later
    command_line = 'GfxFwfit.exe /f "{}" /save origin.xml'.format(Origin_Bin_Path)
    os.system(command_line)

    print(os.listdir())
    print('success')

def Change_Fw_XML():

    ######################################################################################################
    ###  The function will change lines in xml and swap the firmware image then save xml as new file  ####
    ######################################################################################################


    # If you want to modify global variable inside the function, you need to declare variable with "global" character in front of variables
    global Target_Bin_Path,Update_Xml_File,Update_Xml_Name


    # Search the bin file under "Firmware Image" folder
    print('Search the bin file we want to flash: \n')
    os.chdir(Firmware_Path)

    # Search the file under the folder with ".bin" as its extension name
    # Then pass the filepath and filename to global variable (Target_Bin_Path) and (Target_Bin_Name)
    file_ex_name = '.bin'
    for item in os.listdir():
        file_name,file_ext = os.path.splitext(item)
        if os.path.isfile(item) and file_ext == file_ex_name:
            Target_Bin_Name = file_name
            Target_Bin_Path = os.path.join(os.getcwd(),Target_Bin_Name)
            print("New bin file path = ",Target_Bin_Path)
            print("New bin file name = ",item)


    ##### Below function will rename the file with more readable name #####
    # Target_Bin_Name = Graphics_Firmware_DG02_2.2270_production_B-step.bin
    # Target_Bin_Version = 2270 
    # Update_Xml_Name = HA6YA_VBIOS_FW2258_OPROM1051_CBN_0x05a_0617_to_DG02_2.2270
    # Update_Xml_File = HA6YA_VBIOS_FW2258_OPROM1051_CBN_0x05a_0617_to_DG02_2.2270.xml

    start_pos = Target_Bin_Name.find('DG')
    dot_pos = Target_Bin_Name.find('.')
    end_pos = Target_Bin_Name[dot_pos:].find('_')

    Target_Bin_Version = Target_Bin_Name[start_pos:dot_pos + end_pos]

    Update_Xml_Name = "{}_to_{}".format(Origin_Bin_Name,Target_Bin_Version)
    Update_Xml_File = "{}.xml".format(Update_Xml_Name)

    # Copy the origin xml with new xml name
    os.chdir(FIT_path)
    shutil.copyfile('origin.xml', Update_Xml_File)

    tree = ET.parse('origin.xml')
    root = tree.getroot()
    sku_version = root.attrib['sku']
    data['sku_version'] = sku_version
    print("sku version = ",sku_version)

    # OpRomRegion Configure
    OpRomRegion = root.findall('.//OpRomRegion')
    OpRom_File_Path = OpRomRegion[0].find('InputFile').get('value')
    OpRom_Version = OpRomRegion[0].find('Version').get('value')
    data['OpRom_File_Path'] = OpRom_File_Path
    data['OpRom_version'] = OpRom_Version

    # GfxFwRegion Configure
    GfxFwRegion = root.findall('.//GfxFwRegion')
    GfxFw_File_Path = GfxFwRegion[0].find('GfxFwRegionFile').get('value')
    GfxFw_Version = GfxFwRegion[0].find('ExternalVersion').get('value')
    data['GfxFw_File_Path'] = GfxFw_File_Path
    data['GfxFw_Version'] = GfxFw_Version

    # Save some configuration info to json file for check info
    data_path = os.path.join(root_path,'origin_config.json')
    with open(data_path,'w') as f:
        json.dump(data,f,ensure_ascii=False)


    New_File_Name = "{}.xml".format(Origin_Bin_Name)

    try:
        os.rename('origin.xml', New_File_Name)
    except FileExistsError as e:
        pass


    ######################################
    ### Modify new xml with new fw bin ###
    tree = ET.parse(Update_Xml_File)
    root = tree.getroot()

    # Go to GfxFwRegion Configure in XML
    GfxFwRegion = root.findall('.//GfxFwRegion')

    # Change the bin file path with the bin under "Firmware Image" folder
    New_GfxFw_Path = GfxFwRegion[0].find('GfxFwRegionFile')
    New_GfxFw_Path.attrib["value"] = "{}.bin".format(Target_Bin_Path)

    # Also change the version value of the fw
    New_GfxFw_Version = GfxFwRegion[0].find('ExternalVersion')
    New_GfxFw_Version.attrib["value"] = Target_Bin_Version

    tree.write(Update_Xml_File,encoding='UTF-8',xml_declaration=True)
    ######################################


def Change_Memory_XML():
    
    # If you want to modify global variable inside the function, you need to declare variable with "global" character in front of variables
    global Device_Type

    ####### Get Device Type #######

    # This Function will Get Device Type(MB or PC) from command line

    argv = sys.argv[1:]

    opts, args = getopt.getopt(argv,"t:")

    
    # Get the value after -t
    # ex: python main.py -t MRB
    # opts = [('-t','MRB')] , opt = '-t'; arg = 'MRB'
    for opt, arg in opts:
        if opt in ['-t']:
            Device_Type = arg

    ################################


    ###### Get Memory Profile ######

    # This function will Get Three Value(Freq Value, Vendor Name, Binary Filepath) from  Image XML File

    # store the bin file info in "LUT" folder
    bin_list = []
    vendor_list = ['Samsung','Hynix','Micron']

    dir_file = os.listdir(root_path)
    if 'LUT' in dir_file:

        # Go to LUT Folder
        LUT_Path = os.path.join(root_path,'LUT')
        os.chdir(LUT_Path)

        # check item with specific device type(PC or NB)
        for item in os.listdir(LUT_Path):

            if Device_Type in item:

                # Temp Store Three Value(Binary Filepath,Freq Value, Vendor Name) and Store Temp in Bin List
                temp = {}

                # Get Binary Filepath
                # filepath = 'currentpath/filename'
                temp['filepath'] = os.path.join(LUT_Path,item)

                # Get Vendor Name
                # Since the filename are all like below example
                # ex : item = DG2_128_B0_MRB_Hynix_06_16gb_14GT_SBREF_ON_16_02_2022.bin
                # item.split('_') =  ['DG2', '128', 'B0', 'MRB', 'Hynix', '06', '16gb', '14GT', 'SBREF', 'ON', '16', '02', '2022.bin']
                # I split the name with '_' to get Vendor ID (Hynix)
                for each_string in item.split('_'):
                
                    if each_string in vendor_list:
                        temp['vendor'] = each_string

                # Get Freq Value
                # ex : item = "DG2_128_B0_FRD4_Hynix_16gb_15_5GT_SBREF_ON_14_03_2022_rev0_8.bin"
                # we can get the value "15_5GT" from item name and store it to temp['freq'] as integer(15.50)
                first_pos = item.find('gb_')
                second_pos = item.find('_SBREF')

                # item = "15_5GT"
                item = item[first_pos+3:second_pos]

                # item = "15_5"
                item = item.replace("G","")
                item = item.replace("T","")

                # item = "15.5"
                if "_" in item:
                    item = item.replace("_",".")
                
                # item = "15.50"
                if len(item) < 4:
                    item = item + ".00"
                if len(item) < 5:
                    item = item + "0"
                
                temp['freq'] = item
            
                bin_list.append(temp)

        ################################

        #### Change Memory Profile #####
        # This Function will Change Image XML File with Bin Files which are in the LUT Folder

        print('Search the flash file we want to change: \n')

        # Change Path to FIT Folder
        os.chdir(FIT_path)

        # Open XML File
        tree = ET.parse(Update_Xml_File)
        root = tree.getroot()

        # Set Root to Memory Profile Configure
        MemorySettings = root.findall('.//SpdMemorySettings')

        # First Value in MemorySettings which is First Freq Value
        value = (MemorySettings[0][0].attrib)['value'] 

    
        i = 0
        # If Memory Freq is 0.00 then there is no need to change this setting
        while value != "0.00":
            
            # print(i) is for tracing which line we select, we can get freq,vendor and path every 4 lines
            print(i)

            # Get freq,vendor and path every 4 lines
            memory_freq = (MemorySettings[0][i].attrib)['value']
            vender_id = (MemorySettings[0][i+1].attrib)['value']
            binary_path = (MemorySettings[0][i+3].attrib)['value']

            for each_bin in bin_list:

                # Require Same Vendor and Same Freq, then Change the file with new bin 
                if each_bin['vendor'] == vender_id and each_bin['freq'] == memory_freq:

                    print("\noriginal path = ",binary_path)
                    print("new binary path = ",each_bin['filepath'])
                    MemorySettings[0][i+3].attrib['value'] = each_bin['filepath']

                    print("="*20)


            

            i = i + 4
            next_memory_freq = (MemorySettings[0][i].attrib)['value']
            value = next_memory_freq
            
        tree.write(Update_Xml_File,encoding='UTF-8',xml_declaration=True)

def Build_BIN_with_FIT():

    ######################################################################################################
    ############   The function just build image through command line and save the new bin   #############
    ######################################################################################################

    # If you want to modify global variable inside the function, you need to declare variable with "global" character in front of variables
    global New_Bin_Path

    os.chdir(FIT_path)

    commands1 = 'GfxFwfit.exe /f {} /b -o {}.bin'.format(Update_Xml_File,Update_Xml_Name)
    os.system(commands1)

    New_Bin_Path = os.path.join(FIT_path,'{}.bin'.format(Update_Xml_Name))

    os.chdir(FPT_path)
    print('==========',New_Bin_Path)
    print('success')
    






if is_admin():

    print('Step 1 : Store Origin Version XML File')
    Create_XML()
    print('Origin Bin Name = ',Origin_Bin_Name)

    print('Step 2 : Modify XML with new FW Bin')
    Change_Fw_XML()

    print('Step 3 : Modify Memory Profile in XML')
    Change_Memory_XML()
    
    print('Update XML File Name = ',Update_Xml_File)
    
    print('Build New Bin File')
    Build_BIN_with_FIT()

    os.chdir(FPT_path)
    print('Step 4 : Flash FW with New Bin')
    
    commands = 'GfxFwFPTW64.exe -f {} -VERBOSE FPT_Result.txt'.format(New_Bin_Path)
    os.system(commands)
    print('Result Save in Tools/GfxFwFPT/Windows64/ ')

    # Append FPT Result to PreSetting.log
    LOG_PATH = os.path.join(root_path,"PreSetting.log")
    commands = 'type FPT_Result.txt > {}'.format(LOG_PATH)
    os.system(commands)

    print('-----Store Current Status and Reboot-----')
    reboot_commands = 'shutdown -r'
    os.system(reboot_commands)
    
    


else:
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)



