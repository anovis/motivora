
def categorize_response(message):
    no_list = ['no','n']
    yes_list = ['yes','y']
    if message in yes_list:
        return True
