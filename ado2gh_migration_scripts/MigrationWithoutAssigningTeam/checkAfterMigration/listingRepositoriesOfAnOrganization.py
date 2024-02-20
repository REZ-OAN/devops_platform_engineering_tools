import requests
import pandas as pd 
import os
import logging

## get the current directory
c_dir = os.path.dirname(os.path.realpath(__file__))

## ensuring if the error.log file exists or not
if not os.path.exists(f'{c_dir}/error.log'):
    with open(f'{c_dir}/error.log', 'w'):
        pass

## configure logging file
logging.basicConfig(filename=f'{c_dir}/error.log',level=logging.ERROR,format='%(asctime)s - %(levelname)s - %(message)s')
def get_user_repositories(gh_pat,org_name):
    try :
        ## page no
        i = int(1)
        repositories_info = []
        while True :
            # request header
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {gh_pat}",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            ## parameters to pass to the rest api
            params={
                "per_page":100,
                "page":i,
            }
            url = f"https://api.github.com/orgs/{org_name}/repos"
            response = requests.get(url, headers=headers,params=params)
            
            # getting the response into json format
            results = response.json()
            columns = ['id','full_name','isPrivate','git_url','clone_url']

            # if there is no repos in that page then break
            if not results :
                break
            for repository in results :
                repositories_info.append((
                    repository['id'],
                    repository['full_name'],
                    repository['private'],
                    repository['git_url'],
                    repository['clone_url'],
                ));
            i = i + 1
        # creating a dataframe 
        df = pd.DataFrame(data=repositories_info,columns=columns)
        # exporting it into csv
        df.to_csv(f'{c_dir}/orgRepositories.csv',index=False)
    except requests.exceptions.RequestException as e :
        error_msg = f'Error occurred while fetching data : {e}'
        print(error_msg)
        logging.error(error_msg)


if __name__ == "__main__" :

    # GitHub Personal Access Token
    gh_pat = os.environ.get("GH_PAT")
    # Github Organization Name
    org_name = ""
    get_user_repositories(gh_pat,org_name)
