import requests
import os
import pandas as pd
import logging

## get the current directory
c_dir = os.path.dirname(os.path.realpath(__file__))

## creating error.log file
with open(f'{c_dir}/error.log', 'w'):
    pass

## configure logging file
logging.basicConfig(filename=f'{c_dir}/error.log',level=logging.ERROR,format='%(asctime)s - %(levelname)s - %(message)s')


## creating the header and the auth basic auth for azure
def getAuth(ado_pat) :
    ## header config
    headers = {"Content-Type": "application/json"}
    ## for Basic Auth
    auth = ('', ado_pat)
    return (headers,auth)
## listing all of the projects under an organization
def getProjects(organization_name,headers,auth) :
    ## REST API url to get all of the project in that specific organization
    url = f"https://dev.azure.com/{organization_name}/_apis/projects?api-version=7.1-preview.4"
    response = requests.get(url, headers=headers, auth=auth)
    results = response.json()
    project_names = []
    ## storing the project names in our list project_names
    for i in range(len(results['value'])) :
        project_names.append(results['value'][i]['name'])
    return project_names

## we can get repositories either it is disabled or not
def getRepositories(organization_name,project_names,headers,auth) :
        repositories = []
        for i in range(len(project_names)) :
            project_name = project_names[i].replace(' ','%20')
            url = f"https://dev.azure.com/{organization_name}/{project_name}/_apis/git/repositories?api-version=7.2-preview.1" 
            response = requests.get(url,headers=headers,auth=auth)
            results = response.json()
            for j in range(len(results['value'])):
                repositories.append({
                    'project_name':project_names[i],
                    'repo_name':results['value'][j]['name'],
                    'repo_id':results['value'][j]['id']
                })
        return repositories

## listing by last commit information in each branch of a repository
def getLatestUpdatesOfRepositoriesOnEachBranch(organization_name,repositories,headers,auth) :
    ## columns of our generated csv
    column_names = ['project_name','repository_name','branch_name',
                    'repository_id','last_commit_id','haveActivePullRequests',
                    'committer_name','last_commit_date','comment','last_commit_link']
    df = pd.DataFrame()
    for repository in repositories : 
        project_name = repository['project_name'].replace(' ','%20')
        repo_id = repository['repo_id']
        branch = 'master'
        # get the active pull requests
        url1 = f"https://dev.azure.com/{organization_name}/{project_name}/_apis/git/repositories/{repo_id}/pullRequests?searchCriteria.status=active&skip=0"
        response = requests.get(url1,headers=headers,auth=auth)
        results = response.json()
        if response.status_code!=200 and "NotFound" in results['typeKey'] :
            error_msg = f'Repository Is Disabled or You Do Not Have Permission For This Repository : project_name: {repository["project_name"]} repo_name: {repository["repo_name"]},repo_id: {repo_id}'
            print(error_msg)
            logging.error(error_msg)
            continue 
        isActive = response.json()['count']>0
        # get the repository stats for each of the branches
        url2 = f"https://dev.azure.com/{organization_name}/{project_name}/_apis/git/repositories/{repo_id}/stats/branches?api-version=7.1-preview.1"
        response = requests.get(url2,headers=headers,auth=auth)
        results = response.json()
        ## listing the commits of each branch
        for result in results['value'] :
            project_name = repository['project_name']
            repo_name = repository['repo_name']
            # extracting the commit info
            commit_info = result.get('commit', {})
            # extracting the branch name
            branch_name = result.get('name',{})
            commitId = commit_info.get('commitId', '')
            committerName = commit_info.get('committer', {}).get('name', '')
            commitDate = pd.to_datetime(commit_info.get('committer', {}).get('date', ''))
            comment = commit_info.get('comment', '')
            commitURL = commit_info.get('url', '')
            data = [project_name,repo_name,branch_name,repo_id,
                    commitId,isActive,committerName,commitDate,
                    comment,commitURL]
            n_df = pd.DataFrame([data],columns=column_names)
            df = pd.concat([df,n_df],axis=0,ignore_index=True)
    return df
if __name__ == "__main__":
    # add your azure PAT to environment variables
    # export ADO_PAT=your_azure_personal_access_token_here
    ado_pat =  os.environ.get('ADO_PAT')
    organization_name = "udemydevopscourse" 
    # get the authentication and headers 
    headers,auth = getAuth(ado_pat=ado_pat)
    # getting the project names
    project_names = getProjects(organization_name,headers,auth)
    # getting the repositories names
    repositories = getRepositories(organization_name,project_names,headers,auth)
    # get info from the repositories which has master branch as default branch
    df = getLatestUpdatesOfRepositoriesOnEachBranch(organization_name,repositories,headers,auth)
    df = df.sort_values(by="last_commit_date",ascending=False)
    df.to_csv(f'{c_dir}/latest_commit_info.csv',index=False)