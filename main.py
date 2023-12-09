from fastapi import FastAPI
from github_score_12 import *
from get_profile import *
from sonar_crawling import *

import pickle

app = FastAPI()

@app.get("/project/{user}/{project_name}")
def get_score(project_name: str, user: str):
    NAME = project_name
    SC_GH_ORG = NAME.split('/')[0]
    SC_GH_REPO = NAME.split('/')[-1]
    response = get_value_metric(SC_GH_ORG, SC_GH_REPO, SC_ORG, METRIC, SC_TOKEN)

    list_project_score_sc = []

    score = response['component']
    dict_project_score_sc = {'project_name': score['key'].replace('_', '/')}
    for measure in score['measures']:
        dict_project_score_sc[measure['metric']] = measure['value']
    list_project_score_sc.append(dict_project_score_sc)

    with open('sonar_data.pkl', 'rb') as f:
        list_project_score = pickle.load(f)

    list_project_score.extend(list_project_score_sc)

    with open('sonar_data.pkl', 'wb') as f:
        pickle.dump(list_project_score, f)

    return 0

@app.post("/")
def post_score(name: str):
    list_project_name = get_profile_project_list(name)
    if len(list_project_name) < 1:
        print("프로젝트 수 부족")
        return -1
    else:
        list_project_score_gh = []
        for project_name in list_project_name:
            dict_project_score = get_score_main(project_name)
            list_project_score_gh.append(dict_project_score)
            get_score_sonarcloud(name, project_name)

        github_dict = {'project_name': [], 'popularity_watch': [], 'popularity_star': [], 'popularity_fork': [], 'usability_issue': [], \
              'usability_branch': [], 'usability_pr': [], 'usability_tag': [], 'usability_release': [], 'commit_rate_std': [], 'project_size': []}

        for project in github_dict:  # you can list as many input dicts as you want here
            for key, value in project.items():
                github_dict[key].append(value)

        with open('sonar_data.pkl', 'rb') as f:
            list_project_score_sc = pickle.load(f)

        sonar_dict = {'project_name': [], 'complexity': [], 'bugs': [], 'duplicated_lines_density': [], 'code_smells': [], \
               'comment_lines': [], 'cognitive_complexity': [], 'vulnerabilities': []}

        for project in list_project_score_sc:  # you can list as many input dicts as you want here
            for key, value in project.items():
                sonar_dict[key].append(value)

        common_gh_sc_list = list(set(sonar_dict['project_name']) & set(github_dict['project_name']))

        common_gh_sc_dict = {'project_name': [], 'complexity': [], 'bugs': [], 'duplicated_lines_density': [],'code_smells': [], \
                             'comment_lines': [], 'cognitive_complexity': [], 'vulnerabilities': [],'popularity_watch': [], \
                             'popularity_star': [], 'popularity_fork': [], 'usability_issue': [],'usability_branch': [], \
                             'usability_pr': [], 'usability_tag': [], 'usability_release': [], 'commit_rate_std': [], 'project_size': []}

        for common_project in common_gh_sc_list:
            sonar_idx = sonar_dict['project_name'].index(common_project)
            github_idx = github_dict['project_name'].index(common_project)
            common_gh_sc_dict['project_name'].append(common_project)
            for key in list(sonar_dict.keys()):
                if key != 'project_name':
                    common_gh_sc_dict[key].append(sonar_dict[key][sonar_idx])
            for key in list(github_dict.keys()):
                if key != 'project_name':
                    common_gh_sc_dict[key].append(github_dict[key][github_idx])

        df_sc_gh = pd.DataFrame(common_gh_sc_dict)

        with open('project_data_last.pkl', 'wb') as f:
            normalize_data = pickle.load(f)
        df = pd.DataFrame(normalize_data)

        df_concat = pd.concat([df,df_sc_gh])

        for key in list(normalize_data.keys()):
            df_concat = detect_outliers(df_concat, key, 30)

        df_normalization = (df_concat - df_concat.min()) / (df_concat.max() - df_concat.min())

        df_last = pd.DataFrame.to_json(df_normalization)

        return df_last




