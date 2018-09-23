import os
import re
import zipfile36 as zipfile 

def unzip_directory(directory):
    """" This function unzips (and then deletes) all zip files in a directory """
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if re.search(r'\.zip$', filename):
                to_path = os.path.join(root, filename.split('.zip')[0])
                zipped_file = os.path.join(root, filename)
                if not os.path.exists(to_path):
                    os.makedirs(to_path)
                    with zipfile.ZipFile(zipped_file, 'r') as zfile:
                        zfile.extractall(path=to_path)
                    # deletes zip file
                    os.remove(zipped_file)

def exists_zip(directory):
    """ This function returns T/F whether any .zip file exists within the directory, recursively """
    is_zip = False
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if re.search(r'\.zip$', filename):
                is_zip = True
    return is_zip

def unzip_directory_recursively(directory, max_iter=1000):
    """ Calls unzip_directory until all contained zip files (and new ones from previous calls)
    are unzipped
    """
    iterate = 0
    while exists_zip(directory) and iterate < max_iter:
        unzip_directory(directory)
        iterate += 1
    pre = "Did not " if iterate < max_iter else "Did"
    print(pre, "time out based on max_iter limit of", max_iter, ". Took iterations:", iterate)


if __name__ == '__main__':
    import sys
    unzip_directory_recursively(sys.argv[1])